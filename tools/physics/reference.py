#!/usr/bin/env python3
"""Referencyjny model dynamiki M7.

Ground truth i klasyfikacja parametrów są w data/vehicle/m7-spec.json.
Wartości bez źródła pierwotnego pozostają design_model.
"""
import math, json, sys
G=9.80665
MASS={"AW0":170000.0,"AW2":221940.0}
V={
    "b_service":1.10,
    "b_emergency":1.30,
    "jerk":0.75,
    # `max_speed_ms` stalo tu do 02.09.2026 jako 80/3.6 i nie czytalo go NIC — ani ta
    # referencja, ani braking.py, ani testy, ani rdzen C#. Byla to reczna kopia wpisu
    # `max_speed_kmh` z data/vehicle/m7-spec.json (status design_model, source_id null,
    # "Legacy simulator value"), czyli duplikat danych w kodzie w pliku, ktory jest
    # zrodlem parytetu dla C#. braking.py czyta te wielkosc z rejestru i tak ma zostac.
    # Predkosc docelowa jest wszedzie ARGUMENTEM (sim_accel(mass, 80)), a nie stala.
    "F0_N":248900.0,
    "installed_power_W":2160000.0,
    "powered_mass_fraction":4/6,
}

def base_speed_ms():
    """Model transition point implied by design F0 and source-backed installed power."""
    return V["installed_power_W"]/V["F0_N"]

def davis_N(mass_kg,v_ms,tunnel=True):
    v_kmh=v_ms*3.6; c=1.40 if tunnel else 1.00; r=1.5+0.006*v_kmh+0.00035*c*v_kmh*v_kmh
    return r*(mass_kg/1000.0)*G

def traction_N(v_ms,mass_kg,mu=0.25):
    if v_ms<=base_speed_ms():
        f=V["F0_N"]
    else:
        f=V["installed_power_W"]/max(v_ms,0.01)
    adhesion=mu*mass_kg*V["powered_mass_fraction"]*G
    return min(f,adhesion)

def power_kW(): return V["installed_power_W"]/1000

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
        print(f"moc zainstalowana trakcji (spec) = {power_kW():.0f} kW")
        print(f"prędkość przejścia modelu F0→P = {base_speed_ms()*3.6:.2f} km/h (derived design_model)")
        for r in report(): print(r)
