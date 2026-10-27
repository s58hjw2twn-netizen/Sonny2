"""Dependency-free texture energy diagnostic on aligned normalized grayscale crops."""
from math import isfinite

def texture_report(original, restored, *, max_relative_energy_change=0.35):
    if not isinstance(max_relative_energy_change, (int,float)) or not isfinite(max_relative_energy_change) or max_relative_energy_change < 0:
        raise ValueError("invalid tolerance")
    def check(grid):
        if not isinstance(grid,(list,tuple)) or len(grid)<2 or not isinstance(grid[0],(list,tuple)) or len(grid[0])<2:
            raise ValueError("invalid image")
        width=len(grid[0])
        if any(not isinstance(row,(list,tuple)) or len(row)!=width for row in grid):
            raise ValueError("nonrectangular image")
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(v) or not 0<=v<=1 for row in grid for v in row):
            raise ValueError("invalid pixel")
        return len(grid),width
    shape=check(original)
    if check(restored)!=shape:
        raise ValueError("different crop dimensions")
    def energy(grid):
        h,w=shape
        differences=[]
        for y in range(h):
            for x in range(w):
                if x+1<w: differences.append(abs(grid[y][x]-grid[y][x+1]))
                if y+1<h: differences.append(abs(grid[y][x]-grid[y+1][x]))
        return sum(differences)/len(differences)
    before,after=energy(original),energy(restored)
    if before<=1e-12:
        return dict(texture_pass=False,reason="insufficient_original_texture",original_energy=before,restored_energy=after)
    delta=(after-before)/before
    passed=abs(delta)<=max_relative_energy_change
    return dict(texture_pass=passed,reason="within_tolerance" if passed else "texture_energy_changed",relative_energy_change=delta,original_energy=before,restored_energy=after)
