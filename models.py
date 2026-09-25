"""Small, dependency-free numerical helpers used by the reconstruction demos."""
import math
import statistics as st


def finite(value, name='value'):
    x = float(value)
    if not math.isfinite(x):
        raise ValueError(name + ' must be finite')
    return x


def mean(xs):
    return st.mean(xs)


def quantile(xs, p):
    a = sorted(xs)
    pos = (len(a)-1)*p
    lo = int(pos)
    return a[lo] + (a[min(lo+1, len(a)-1)]-a[lo])*(pos-lo)


def fit_ridge(rows, targets, penalty=1.0):
    """Standardization is fitted only on training rows; intercept is unpenalized."""
    if len(rows) < 2 or len(rows) != len(targets):
        raise ValueError('At least two aligned training observations are required')
    width = len(rows[0])
    if not width or any(len(r) != width for r in rows):
        raise ValueError('Feature dimensions must agree')
    centers = [mean([r[j] for r in rows]) for j in range(width)]
    scales = [st.pstdev([r[j] for r in rows]) or 1 for j in range(width)]
    x = [[1]+[(r[j]-centers[j])/scales[j] for j in range(width)] for r in rows]
    n = width+1
    a = [[sum(r[i]*r[j] for r in x)+(penalty if i == j and i else 0) for j in range(n)] + [sum(r[i]*y for r,y in zip(x,targets))] for i in range(n)]
    for i in range(n):
        pivot = max(range(i,n),key=lambda k:abs(a[k][i]))
        a[i],a[pivot] = a[pivot],a[i]
        if abs(a[i][i]) < 1e-12:
            raise ValueError('Singular model; add more varied observations')
        div = a[i][i]
        a[i] = [v/div for v in a[i]]
        for k in range(n):
            if k != i:
                factor = a[k][i]
                a[k] = [u-factor*v for u,v in zip(a[k],a[i])]
    return {'coefficients':[r[-1] for r in a], 'centers':centers, 'scales':scales}


def predict(model, row):
    return model['coefficients'][0]+sum(c*(x-m)/s for c,x,m,s in zip(model['coefficients'][1:],row,model['centers'],model['scales']))
