"""GoPro lens model from the clip's own GPMF metadata (POLY + ZMPL), used for fisheye -> rectilinear remapping.

theta(rad) = POLY(ZMPL * r), r = 1 at the half-diagonal. Call load_from_clip(path) before maps()/fit_scale();
the defaults below are a HERO11 Wide 4K 16:9 clip and are only a fallback.
"""
import numpy as np, struct
POLY = np.array([0.0, 1.8151302337646484, 0.10589481890201569, -0.6546851396560669, 0.35023391246795654])
ZMPL = 0.6314452886581421
_rr = np.linspace(0, 1.3, 20001)
def theta_of_r(r): x = ZMPL * np.asarray(r, float); return sum(c * x ** i for i, c in enumerate(POLY))
_tt = theta_of_r(_rr)
def r_of_theta(t): return np.interp(t, _tt, _rr)

def read_gpmf_lens(path):
    """Return dict(VFOV, POLY, ZMPL) read from the GPMF block near the start/end of a GoPro MP4."""
    import os
    with open(path, 'rb') as f:
        d = f.read(4_000_000); f.seek(max(0, os.path.getsize(path) - 3_000_000)); d += f.read()
    out = {}
    for key in (b'VFOV', b'POLY', b'ZMPL'):
        i = d.find(key)
        if i < 0: continue
        t = chr(d[i + 4]); sz = d[i + 5]; rep = struct.unpack('>H', d[i + 6:i + 8])[0]; raw = d[i + 8:i + 8 + sz * rep]
        out[key.decode()] = raw.decode('latin1').strip() if t == 'c' else list(struct.unpack('>' + 'f' * (len(raw) // 4), raw[:len(raw) // 4 * 4]))
    return out

def load_from_clip(path):
    """Set POLY/ZMPL from the clip. Returns the lens mode letter (W wide, S superview, L linear, ...)."""
    global POLY, ZMPL, _tt
    info = read_gpmf_lens(path)
    if 'POLY' in info and 'ZMPL' in info:
        POLY = np.array(info['POLY']); ZMPL = float(info['ZMPL'][0]); _tt = theta_of_r(_rr)
    return info.get('VFOV')
def project(theta,a):
    # output radius family: a=1 rectilinear (tan), a->0 equidistant (~fisheye)
    return np.tan(a*theta)/a if a>1e-6 else theta
def fit_scale(a,W=3840,H=2160):
    # largest output zoom s such that every output border pixel maps inside source
    D=np.hypot(W/2,H/2)
    # border sample points (normalized to half-diagonal)
    xs=np.linspace(-W/2,W/2,400); ys=np.linspace(-H/2,H/2,400)
    pts=np.concatenate([np.stack([xs,np.full_like(xs,H/2)],1),np.stack([np.full_like(ys,W/2),ys],1)])/D
    ro=np.hypot(pts[:,0],pts[:,1]); 
    # output radius ro corresponds to projected value ro*K where K = project(theta_c)/1 ; search K
    lo,hi=0.01,10
    for _ in range(60):
        K=(lo+hi)/2; t=np.arctan(ro*K*a)/a if a>1e-6 else ro*K
        ri=r_of_theta(t)
        # source point along same direction, must be inside source rect
        sx=np.abs(pts[:,0]/ro*ri)*D; sy=np.abs(pts[:,1]/ro*ri)*D
        ok=(sx<=W/2-1).all() and (sy<=H/2-1).all()
        lo,hi=(K,hi) if ok else (lo,K)
    return lo
def maps(a,W=3840,H=2160,extra=1.0,dx=0.0,dy=0.0,rot=0.0):
    K=fit_scale(a,W,H)/extra; D=np.hypot(W/2,H/2)
    yy,xx=np.mgrid[0:H,0:W].astype(np.float64)
    X=(xx-(W-1)/2)/D; Y=(yy-(H-1)/2)/D
    if rot: c,s=np.cos(rot),np.sin(rot); X,Y=c*X-s*Y,s*X+c*Y
    X+=dx; Y+=dy
    ro=np.hypot(X,Y)+1e-12
    t=np.arctan(ro*K*a)/a if a>1e-6 else ro*K
    ri=r_of_theta(t)
    sx=X/ro*ri*D+(W-1)/2; sy=Y/ro*ri*D+(H-1)/2
    return sx,sy
def write_pgm(path,arr):
    a=np.clip(np.round(arr),0,65535).astype('>u2'); H,W=a.shape
    with open(path,'wb') as f: f.write(f'P5\n{W} {H}\n65535\n'.encode()); f.write(a.tobytes())
if __name__=='__main__':
    print('theta corner deg', np.degrees(theta_of_r(1.0)))
    for a in (1.0,0.8,0.6,0.4):
        K=fit_scale(a); D=1
        tc=np.degrees(np.arctan(K*a)/a)
        th=np.degrees(np.arctan(0.8716*K*a)/a); tv=np.degrees(np.arctan(0.4903*K*a)/a)
        print(f'a={a}: out diag FOV {2*tc:.1f}, HFOV {2*th:.1f}, VFOV {2*tv:.1f}, centre zoom {1/(K/ (1.8151*ZMPL)):.2f}x')

def required_zoom(a=1.0, rot_deg=0.0, dx=0.0, dy=0.0, W=3840, H=2160, margin_px=2):
    """Smallest extra zoom so every output border pixel samples inside the source."""
    K=fit_scale(a,W,H); D=np.hypot(W/2,H/2)
    xs=np.linspace(-W/2,W/2,200)/D; ys=np.linspace(-H/2,H/2,120)/D
    B=np.concatenate([xs+1j*ys[0],xs+1j*ys[-1],xs[0]+1j*ys,xs[-1]+1j*ys])
    q=B*np.exp(1j*np.radians(rot_deg))+complex(dx,dy)
    def over(z):
        c=q/z; r=np.abs(c); t=np.arctan(r*K*a)/a; ri=r_of_theta(t); p=c/r*ri*D
        return max(np.max(np.abs(p.real))-(W/2-margin_px), np.max(np.abs(p.imag))-(H/2-margin_px))
    lo,hi=0.9,2.0
    for _ in range(50):
        m=(lo+hi)/2
        if over(m)<=0: hi=m
        else: lo=m
    return hi
