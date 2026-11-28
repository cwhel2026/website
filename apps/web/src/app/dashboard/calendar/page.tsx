"use client";
import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { getToken } from "@/lib/auth-client";
type Appt = {id:string;job_id:string;job_reference:string;appointment_type:string;status:string;scheduled_start:string;scheduled_end:string;postcode:string|null};
type Hint = {appointment_id:string;job_reference:string;drive_minutes_from_previous:number|null;available_gap_minutes:number|null;travel_conflict:boolean|null};
const londonDay = () => new Intl.DateTimeFormat("en-CA",{timeZone:"Europe/London",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date());
export default function CalendarPage(){
 const [items,setItems]=useState<Appt[]|null>(null);
 const [hints,setHints]=useState<Hint[]|null>(null);
 const [day,setDay]=useState(londonDay);
 const [error,setError]=useState("");
 const [move,setMove]=useState("");
 const [busy,setBusy]=useState(false);
 const reload=()=>{const token=getToken();if(!token)return;const from=new Date();from.setDate(from.getDate()-1);const to=new Date();to.setDate(to.getDate()+14);
 apiGet<Appt[]>(`/api/v1/calendar/appointments?from=${from.toISOString()}&to=${to.toISOString()}`,token).then(setItems).catch(()=>{setItems(null);setError("Calendar unavailable")});};
 useEffect(reload,[]);
 useEffect(()=>{const token=getToken();setHints(null);if(token&&day)apiGet<{appointments:Hint[]}>(`/api/v1/calendar/route-review?day=${day}`,token).then(r=>setHints(r.appointments)).catch(()=>setError("Route review unavailable"));},[day]);
 async function reschedule(a:Appt){const token=getToken();if(!token||!move||!window.confirm("Confirm new appointment time? Customer notification is not sent."))return;setBusy(true);setError("");try{await apiPost(`/api/v1/jobs/${a.job_id}/appointments/${a.id}/reschedule`,{scheduled_start:new Date(move).toISOString(),confirmed:true},token);reload();setHints(null);setMove("");}catch(e){setError(e instanceof Error?e.message:"Reschedule failed");}finally{setBusy(false);}}
 return <div className="max-w-3xl space-y-5 pb-16"><header className="rounded-2xl bg-slate-950 p-6 text-white"><p className="text-xs uppercase tracking-widest text-amber-300">SurfaceCoat · Operations</p><h1 className="mt-2 text-2xl font-semibold portal-department-title">Intelligent diary</h1><p className="mt-2 text-sm text-slate-300">Weather-safe visits and travel review</p></header>{error&&<p role="alert" className="rounded border p-3 text-red-700">{error}</p>}<section className="rounded-xl border p-4"><h2 className="font-semibold">Daily route review</h2><input aria-label="Route date" type="date" value={day} onChange={e=>setDay(e.target.value)} className="mt-2 rounded border p-2"/><p className="mt-2 text-xs text-slate-500">Geographic estimates, not live road traffic.</p>{hints===null?<p>Route data unavailable or loading.</p>:hints.length===0?<p>No confirmed visits.</p>:hints.map(h=><div key={h.appointment_id} className="mt-2 rounded border p-3 text-sm">{h.job_reference} · {h.drive_minutes_from_previous??"Unknown"} min travel {h.travel_conflict===true&&<strong className="block text-red-700">Insufficient travel gap</strong>}</div>)}</section><section className="rounded-xl border p-4"><h2 className="font-semibold">Upcoming appointments</h2>{items===null?<p>Calendar unavailable or loading.</p>:items.length===0?<p>No appointments scheduled.</p>:items.map(a=><details key={a.id} className="mt-2 rounded border p-3 text-sm"><summary>{a.job_reference} · {a.appointment_type} · {a.status}</summary><p>{new Date(a.scheduled_start).toLocaleString("en-GB",{timeZone:"Europe/London"})} · {a.postcode}</p>{["confirmed","provisional","weather_delayed"].includes(a.status)&&<div className="mt-2 space-y-2"><label className="block">New time (device local)<input type="datetime-local" value={move} onChange={e=>setMove(e.target.value)} className="block w-full rounded border p-2"/></label><button disabled={busy||!move} onClick={()=>reschedule(a)} className="rounded bg-slate-900 px-3 py-2 text-white">Review and reschedule</button></div>}</details>)}</section></div>;
}
