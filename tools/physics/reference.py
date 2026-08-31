#!/usr/bin/env python3
"""Referencyjny, projektowy model dynamiki M7. Parametry est/design wymagają kalibracji."""
import math, json, sys
G=9.80665
MASS={"AW0":155000.0,"AW2":206940.0}
V={"b_service":1.10,"b_emergency":1.30,"jerk":0.75,"base_speed_ms":35/3.6,"max_speed_ms":80/3.6,"F0_N":248900.0}

def davis_N(mass_kg,v_ms,tunnel=True):
    v_kmh=v_ms*3.6; c=1.40 if tunnel else 1.00; r=1.5+0.006*v_kmh+0.00035*c*v_kmh*v_kmh
    return r*(mass_kg/1000.0)*G

def traction_N(v_ms,mass_kg,mu=0.25):
    f=V["F0_N"] if v_ms<=V["base_speed_ms"] else V["F0_N"]*V["base_speed_ms"]/max(v_ms,0.01)
    adhesion=mu*mass_kg*(4/6)*G
    return min(f,adhesion)

def power_kW(): return V["F0_N"]*V["base_speed_ms"]/1000

def sim_accel(mass_kg,target_kmh,grade_pct=0.0,mu=0.25,dt=1/120):
    v=s=t=0.0; target=target_kmh/3.6; eff_mass=mass_kg*1.08
    while v<target and t<300:
        force=traction_N(v,mass_kg,mu)-davis_N(mass_kg,v)-mass_kg*G*grade_pct/100
        a=max(0.0,force/eff_mass); v=min(target,v+a*dt); s+=v*dt; t+=dt
    return t,s

def sim_brake(mass_kg,start_kmh,decel,dt=1/120):
    v=start_kmh/3.6; s=t=0.0; a=0.0
    while v>0 and t<120:
        a=min(decel,a+V["jerk"]*dt); v=max(0.0,v-a*dt); s+=v*dt; t+=dt
    return t,s

def report():
    rows=[]
    for load,m in MASS.items():
        t,s=sim_accel(m,80); rows.append({"case":"accel_0_80","load":load,"time_s":round(t,1),"distance_m":round(s,1)})
    for load,m in MASS.items():
        t,s=sim_brake(m,80,V["b_service"]); rows.append({"case":"brake_service_80_0","load":load,"time_s":round(t,1),"distance_m":round(s,1)})
    return rows

if __name__=="__main__":
    if "--json" in sys.argv: print(json.dumps(report(),ensure_ascii=False,indent=2))
    else:
        print(f"moc trakcyjna (model) ≈ {power_kW():.0f} kW")
        for r in report(): print(r)
