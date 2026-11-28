"use client";
import {useEffect,useState} from "react";
import {apiGet,apiPost} from "@/lib/api";
import {getToken} from "@/lib/auth-client";
import {PortalPageTitle,PortalError,PortalKpi} from "@/components/portal-ui";
type Approval={id:string;approval_type:string;title:string;summary:string|null;status:string};
export default function ApprovalsPage(){
 const [items,setItems]=useState<Approval[]|null>(null);
 const [error,setError]=useState("");
 const [busy,setBusy]=useState(false);
 const [filter,setFilter]=useState("pending");
 const [note,setNote]=useState("");
 async function reload(){const token=getToken();if(!token){setError("Session unavailable");return;}try{setItems(await apiGet<Approval[]>("/api/v1/approvals",token));}catch{setItems(null);setError("Approval data unavailable");}}
 useEffect(()=>{void reload()},[]);
 async function decide(a:Approval,action:"approve"|"reject"){if(busy||a.status!=="pending"||!window.confirm(`Confirm ${action}: ${a.title}?`))return;setBusy(true);setError("");try{await apiPost(`/api/v1/approvals/${a.id}/${action}`,{note},getToken()??undefined);setNote("");await reload();}catch(e){setError(e instanceof Error?e.message:"Decision failed");}finally{setBusy(false);}}
 const visible=items?.filter(a=>filter==="all"||a.status===filter);
 return <div className="space-y-4"><PortalPageTitle title="Approval centre" subtitle="Review decisions before authorising business actions."/><div className="grid grid-cols-2 gap-3"><PortalKpi label="Pending" value={items?String(items.filter(a=>a.status==="pending").length):"—"}/><PortalKpi label="Recorded decisions" value={items?String(items.filter(a=>a.status!=="pending").length):"—"}/></div>{error&&<PortalError message={error}/>}<div className="flex flex-wrap gap-2"><button onClick={()=>setFilter("pending")} aria-pressed={filter==="pending"} className="portal-filter">Pending</button><button onClick={()=>setFilter("all")} aria-pressed={filter==="all"} className="portal-filter">All decisions</button><button onClick={()=>void reload()} className="portal-filter">Refresh</button></div>{visible===undefined?<p role="status">Approval data loading or unavailable.</p>:visible.length===0?<p>No matching approvals.</p>:visible.map(a=><article key={a.id} className="portal-panel"><p className="text-xs uppercase tracking-wide text-amber-300">{a.approval_type.replaceAll("_"," ")} · {a.status}</p><h2 className="mt-2 font-semibold">{a.title}</h2>{a.summary&&<p className="mt-2 whitespace-pre-wrap break-words text-sm text-white/80">{a.summary}</p>}{a.status==="pending"&&<div className="mt-4 space-y-2"><label className="block text-sm">Decision note<input value={note} onChange={e=>setNote(e.target.value)} className="mt-1 w-full rounded border border-white/20 bg-black/20 p-3"/></label><div className="flex gap-2"><button disabled={busy} onClick={()=>void decide(a,"approve")} className="min-h-11 flex-1 rounded-lg bg-amber-400 font-semibold text-black">Approve</button><button disabled={busy} onClick={()=>void decide(a,"reject")} className="portal-filter flex-1">Reject</button></div></div>}</article>)}</div>;
}
