import axios from 'axios';
import {
  AlertTriangle,
  Check,
  CircleDollarSign,
  Clock,
  FileCheck,
  LogOut,
  PackagePlus,
  RefreshCw,
  Shield,
  Truck,
  Upload,
  UserPlus,
  Users,
} from 'lucide-react';
import type { ReactNode } from 'react';
import { FormEvent, useEffect, useMemo, useState } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const API_ROOT = API.replace(/\/api\/v1\/?$/, '');
const api = axios.create({ baseURL: API });

type User = {
  id: number;
  email: string;
  name: string;
  account_type: 'broker' | 'carrier' | 'shipper';
  organization_id: number | null;
  organization_name: string | null;
  role: string | null;
  is_admin: boolean;
  permissions: string[];
};

type Load = {
  id: number;
  reference: string;
  shipper: string;
  shipper_user_id: number;
  carrier_org_id: number | null;
  carrier: string | null;
  origin: string;
  destination: string;
  equipment_type: string;
  commodity: string;
  status: string;
  compliance_flag: boolean;
  compliance_reason: string | null;
  rate: null | { id: number; version: number; base_rate: number; accessorials: unknown[] };
  pod: null | { id: number; file_name: string; url: string; verified_at: string | null };
};

type Org = { id: number; name: string; type: string };
type Role = { id: number; name: string; permissions: string[] };
type Shipper = { id: number; name: string; email: string };
type AuditRow = { id: number; action: string; entity_type?: string; entity_id?: number; details?: Record<string, unknown>; created_at: string; user_id?: number };
type HistoryRow = { id: number; from_status: string | null; to_status: string; note: string | null; created_at: string; changed_by_user_id: number | null };
type AppMutate = (label: string, fn: () => Promise<unknown>) => Promise<void>;

const demoAccounts = [
  ['Broker Admin', 'broker.admin@loadflow.test'],
  ['Broker Dispatcher', 'dispatcher@loadflow.test'],
  ['Carrier Admin', 'carrier.admin@loadflow.test'],
  ['Carrier Driver', 'driver@loadflow.test'],
  ['Shipper', 'shipper@loadflow.test'],
];

const nextStatus: Record<string, string> = {
  'Rate Confirmed': 'Dispatched',
  Dispatched: 'In Transit',
  'In Transit': 'Delivered',
  'POD Verified': 'Invoiced/Closed',
};

function App() {
  const [token, setToken] = useState(localStorage.getItem('loadflow_token') || '');
  const [user, setUser] = useState<User | null>(null);
  const [loads, setLoads] = useState<Load[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [orgs, setOrgs] = useState<Org[]>([]);
  const [shippers, setShippers] = useState<Shipper[]>([]);
  const [permissions, setPermissions] = useState<{ code: string; description: string }[]>([]);
  const [auditRows, setAuditRows] = useState<AuditRow[]>([]);
  const [query, setQuery] = useState('');
  const [message, setMessage] = useState('');
  const [selectedLoad, setSelectedLoad] = useState<Load | null>(null);

  useEffect(() => {
    api.defaults.headers.common.Authorization = token ? `Bearer ${token}` : '';
    if (token) refresh();
  }, [token]);

  async function refresh() {
    try {
      const me = await api.get('/auth/me');
      setUser(me.data);
      const [loadRes, permRes] = await Promise.all([
        api.get('/loads', { params: { q: query || undefined } }),
        api.get('/permissions'),
      ]);
      setLoads(loadRes.data);
      setPermissions(permRes.data);

      if (me.data.account_type !== 'shipper') {
        const [roleRes, orgRes, auditRes] = await Promise.all([
          api.get('/roles').catch(() => ({ data: [] })),
          api.get('/organizations', { params: { type: 'carrier' } }).catch(() => ({ data: [] })),
          api.get('/audit').catch(() => ({ data: [] })),
        ]);
        setRoles(roleRes.data);
        setOrgs(orgRes.data);
        setAuditRows(auditRes.data);
      }
      if (me.data.account_type === 'broker') {
        const shipperRes = await api.get('/users/shippers').catch(() => ({ data: [] }));
        setShippers(shipperRes.data);
      }
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Could not refresh data');
    }
  }

  async function login(email: string, password = 'Password123') {
    try {
      const res = await api.post('/auth/login', { email, password });
      localStorage.setItem('loadflow_token', res.data.access_token);
      setToken(res.data.access_token);
      setUser(res.data.user);
      setMessage(`Signed in as ${res.data.user.name}`);
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Login failed');
    }
  }

  async function mutate(label: string, fn: () => Promise<unknown>) {
    try {
      await fn();
      setMessage(label);
      await refresh();
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Action failed');
    }
  }

  const stats = useMemo(() => ({
    active: loads.filter((load) => !['Delivered', 'POD Verified', 'Invoiced/Closed'].includes(load.status)).length,
    flagged: loads.filter((load) => load.compliance_flag).length,
    delivered: loads.filter((load) => ['Delivered', 'POD Verified', 'Invoiced/Closed'].includes(load.status)).length,
  }), [loads]);

  if (!token || !user) {
    return <LoginScreen onLogin={login} message={message} />;
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">LoadFlow</p>
          <h1>{user.account_type === 'broker' ? 'Broker load board' : user.account_type === 'carrier' ? 'Carrier operations' : 'Shipment tracker'}</h1>
          <p className="muted">{user.name} / {user.organization_name || 'Shipper account'} / {user.role}</p>
        </div>
        <button className="iconButton" onClick={() => { localStorage.removeItem('loadflow_token'); setToken(''); setUser(null); }}>
          <LogOut size={18} /> Sign out
        </button>
      </header>

      <section className="metrics">
        <Metric icon={<Truck />} label="Active loads" value={stats.active} />
        <Metric icon={<AlertTriangle />} label="Compliance alerts" value={stats.flagged} tone={stats.flagged ? 'warn' : 'ok'} />
        <Metric icon={<FileCheck />} label="Delivered or closed" value={stats.delivered} />
      </section>

      {message && <div className="notice">{message}</div>}

      {user.account_type === 'broker' && (
        <BrokerTools
          user={user}
          shippers={shippers}
          carriers={orgs}
          roles={roles}
          permissions={permissions.map((p) => p.code)}
          query={query}
          setQuery={setQuery}
          refresh={refresh}
          mutate={mutate}
        />
      )}

      {user.account_type === 'carrier' && user.permissions.includes('staff.manage') && (
        <CarrierTools user={user} mutate={mutate} />
      )}

      <section className="section">
        <div className="sectionHead">
          <h2>{user.account_type === 'shipper' ? 'My loads' : 'Loads'}</h2>
          <button className="iconButton quiet" onClick={refresh}><RefreshCw size={16} /> Refresh</button>
        </div>
        <div className="loadGrid">
          {loads.map((load) => (
            <article className="loadCard" key={load.id}>
              <div className="cardTop" onClick={() => setSelectedLoad(load)}>
                <strong>{load.reference}</strong>
                <span className={`pill ${load.compliance_flag ? 'danger' : 'good'}`}>{load.compliance_flag ? 'Flagged' : load.status}</span>
              </div>
              <p className="lane">{load.origin} to {load.destination}</p>
              <p className="muted">{load.equipment_type} / {load.commodity} / {load.carrier || 'Unassigned'}</p>
              {load.compliance_reason && <p className="alertText">{load.compliance_reason}</p>}
              <LoadActions user={user} load={load} carriers={orgs} mutate={mutate} />
            </article>
          ))}
        </div>
      </section>

      {user.account_type !== 'shipper' && <AuditViewer rows={auditRows} />}
      {selectedLoad && <LoadDrawer load={selectedLoad} user={user} mutate={mutate} onClose={() => setSelectedLoad(null)} />}
    </main>
  );
}

function LoginScreen({ onLogin, message }: { onLogin: (email: string, password?: string) => void; message: string }) {
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    onLogin(String(data.email), String(data.password));
  }

  return (
    <main className="login">
      <section className="loginPanel">
        <p className="eyebrow">LoadFlow</p>
        <h1>Freight brokerage operations</h1>
        <form className="manualLogin" onSubmit={submit}>
          <input name="email" type="email" placeholder="Email" defaultValue="broker.admin@loadflow.test" required />
          <input name="password" type="password" placeholder="Password" defaultValue="Password123" required />
          <button><Users size={18} /> Sign in</button>
        </form>
        <p className="muted">Seeded demo users all use <code>Password123</code>.</p>
        <div className="demoGrid">
          {demoAccounts.map(([label, email]) => (
            <button key={email} type="button" onClick={() => onLogin(email)}>
              <Users size={18} />
              <span>{label}</span>
              <small>{email}</small>
            </button>
          ))}
        </div>
        {message && <div className="notice">{message}</div>}
      </section>
    </main>
  );
}

function Metric({ icon, label, value, tone }: { icon: ReactNode; label: string; value: number; tone?: string }) {
  return <div className={`metric ${tone || ''}`}>{icon}<span>{label}</span><strong>{value}</strong></div>;
}

function BrokerTools(props: {
  user: User;
  shippers: Shipper[];
  carriers: Org[];
  roles: Role[];
  permissions: string[];
  query: string;
  setQuery: (value: string) => void;
  refresh: () => void;
  mutate: AppMutate;
}) {
  const can = (permission: string) => props.user.permissions.includes(permission);
  return (
    <section className="tools">
      <form onSubmit={(event) => { event.preventDefault(); props.refresh(); }} className="tool">
        <h2>Search board</h2>
        <input value={props.query} onChange={(e) => props.setQuery(e.target.value)} placeholder="Reference, city, commodity" />
        <button><RefreshCw size={16} /> Search</button>
      </form>
      {can('load.create') && <CreateLoad shippers={props.shippers} mutate={props.mutate} />}
      {can('staff.manage') && <CreateRole permissions={props.permissions} mutate={props.mutate} />}
      {can('staff.manage') && <CreateStaff roles={props.roles} mutate={props.mutate} />}
      {can('staff.manage') && <ComplianceForm carriers={props.carriers} mutate={props.mutate} />}
    </section>
  );
}

function CreateLoad({ shippers, mutate }: { shippers: Shipper[]; mutate: AppMutate }) {
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    await mutate('Load created', () => api.post('/loads', {
      reference: data.reference,
      shipper_user_id: Number(data.shipper_user_id),
      origin: data.origin,
      destination: data.destination,
      equipment_type: data.equipment_type,
      commodity: data.commodity,
    }));
    event.currentTarget.reset();
  }
  return (
    <form className="tool" onSubmit={submit}>
      <h2><PackagePlus size={17} /> New load</h2>
      <input name="reference" placeholder="Reference" required />
      <select name="shipper_user_id" required>
        <option value="">Select shipper</option>
        {shippers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
      </select>
      <input name="origin" placeholder="Origin" required />
      <input name="destination" placeholder="Destination" required />
      <select name="equipment_type"><option>Dry Van</option><option>Reefer</option><option>Flatbed</option></select>
      <select name="commodity"><option>Retail</option><option>Food</option><option>Steel</option></select>
      <button><PackagePlus size={16} /> Create</button>
    </form>
  );
}

function CreateRole({ permissions, mutate }: { permissions: string[]; mutate: AppMutate }) {
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await mutate('Role created', () => api.post('/roles', { name: form.get('name'), permissions: form.getAll('permissions') }));
    event.currentTarget.reset();
  }
  return (
    <form className="tool" onSubmit={submit}>
      <h2><Shield size={17} /> Custom role</h2>
      <input name="name" placeholder="Role name" required />
      <div className="checks">{permissions.map((p) => <label key={p}><input type="checkbox" name="permissions" value={p} /> {p}</label>)}</div>
      <button><Shield size={16} /> Save role</button>
    </form>
  );
}

function CreateStaff({ roles, mutate }: { roles: Role[]; mutate: AppMutate }) {
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    await mutate('Staff user created', () => api.post('/users/staff', { ...data, role_id: Number(data.role_id), password: data.password || 'Password123' }));
    event.currentTarget.reset();
  }
  return (
    <form className="tool" onSubmit={submit}>
      <h2><UserPlus size={17} /> Invite staff</h2>
      <input name="name" placeholder="Name" required />
      <input name="email" type="email" placeholder="Email" required />
      <input name="password" type="password" placeholder="Temp password" defaultValue="Password123" required />
      <select name="role_id" required>
        <option value="">Select role</option>
        {roles.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
      </select>
      <button><UserPlus size={16} /> Create staff</button>
    </form>
  );
}

function ComplianceForm({ carriers, mutate }: { carriers: Org[]; mutate: AppMutate }) {
  const [carrierId, setCarrierId] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    await mutate('Compliance record saved', () => api.post('/compliance', {
      carrier_org_id: Number(data.carrier_org_id),
      insurance_expiry: data.insurance_expiry,
      authority_status: data.authority_status,
      approved_equipment: String(data.approved_equipment).split(',').map((x) => x.trim()).filter(Boolean),
      approved_commodities: String(data.approved_commodities).split(',').map((x) => x.trim()).filter(Boolean),
    }));
  }

  async function removeCompliance() {
    if (!carrierId) return;
    await mutate('Compliance record deleted', () => api.delete(`/compliance/${carrierId}`));
  }

  return (
    <form className="tool" onSubmit={submit}>
      <h2><Check size={17} /> Compliance</h2>
      <select name="carrier_org_id" value={carrierId} onChange={(event) => setCarrierId(event.target.value)} required>
        <option value="">Select carrier</option>
        {carriers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
      </select>
      <input type="date" name="insurance_expiry" required />
      <select name="authority_status"><option>active</option><option>pending</option><option>lapsed</option></select>
      <input name="approved_equipment" defaultValue="Dry Van, Reefer" />
      <input name="approved_commodities" defaultValue="Retail, Food" />
      <div className="splitActions">
        <button><Check size={16} /> Save</button>
        <button type="button" className="dangerButton" onClick={removeCompliance} disabled={!carrierId}>Delete</button>
      </div>
    </form>
  );
}

function CarrierTools({ user, mutate }: { user: User; mutate: AppMutate }) {
  return (
    <section className="tools single">
      <ComplianceForm carriers={[{ id: user.organization_id!, name: user.organization_name || 'Carrier', type: 'carrier' }]} mutate={mutate} />
    </section>
  );
}

function LoadActions({ user, load, carriers, mutate }: { user: User; load: Load; carriers: Org[]; mutate: AppMutate }) {
  const can = (permission: string) => user.permissions.includes(permission);
  return (
    <div className="actionsPanel">
      {user.account_type === 'broker' && load.status === 'Posted' && can('load.assign_carrier') && (
        <AssignCarrierForm load={load} carriers={carriers} mutate={mutate} />
      )}
      {user.account_type === 'carrier' && load.status === 'Carrier Assigned' && can('load.update_status') && (
        <CarrierDecisionActions load={load} mutate={mutate} />
      )}
      {user.account_type === 'broker' && load.compliance_flag && can('load.override_compliance_flag') && (
        <button onClick={() => mutate('Compliance overridden', () => api.post(`/loads/${load.id}/override-compliance`))}><Shield size={15} /> Override compliance</button>
      )}
      {user.account_type === 'broker' && load.status === 'Carrier Assigned' && !load.compliance_flag && can('rate.confirm') && (
        <RateForm load={load} mutate={mutate} />
      )}
      {can('load.update_status') && nextStatus[load.status] && (
        <button onClick={() => mutate(`Moved to ${nextStatus[load.status]}`, () => api.post(`/loads/${load.id}/status`, { status: nextStatus[load.status] }))}><Check size={15} /> Move to {nextStatus[load.status]}</button>
      )}
      {load.status === 'Delivered' && can('pod.upload') && <PodUploadForm load={load} mutate={mutate} />}
      {user.account_type === 'broker' && load.status === 'Delivered' && load.pod && (
        <button onClick={() => mutate('POD verified', () => api.post(`/pod/${load.id}/verify`))}><FileCheck size={15} /> Verify POD</button>
      )}
      {load.pod && <PodLink pod={load.pod} />}
    </div>
  );
}

function CarrierDecisionActions({ load, mutate }: { load: Load; mutate: AppMutate }) {
  return (
    <div className="splitActions">
      <button onClick={() => mutate('Load accepted', () => api.post(`/loads/${load.id}/carrier-decision`, { decision: 'accepted' }))}><Check size={15} /> Accept</button>
      <button className="dangerButton" onClick={() => mutate('Load declined', () => api.post(`/loads/${load.id}/carrier-decision`, { decision: 'declined' }))}>Decline</button>
    </div>
  );
}

function AssignCarrierForm({ load, carriers, mutate }: { load: Load; carriers: Org[]; mutate: AppMutate }) {
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    await mutate('Carrier assigned', () => api.post(`/loads/${load.id}/assign-carrier`, { carrier_org_id: Number(data.carrier_org_id) }));
  }
  return (
    <form className="inlineForm" onSubmit={submit}>
      <select name="carrier_org_id" required>
        <option value="">Carrier</option>
        {carriers.map((carrier) => <option key={carrier.id} value={carrier.id}>{carrier.name}</option>)}
      </select>
      <button><Truck size={15} /> Assign</button>
    </form>
  );
}

function RateForm({ load, mutate }: { load: Load; mutate: AppMutate }) {
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    const accessorials = String(data.accessorials || '')
      .split(',')
      .map((name) => name.trim())
      .filter(Boolean)
      .map((name) => ({ name, amount: 0 }));
    await mutate('Rate confirmed', () => api.post(`/loads/${load.id}/rate-confirmations`, {
      base_rate: Number(data.base_rate),
      accessorials,
    }));
  }
  return (
    <form className="inlineForm" onSubmit={submit}>
      <input name="base_rate" type="number" min="1" step="0.01" placeholder="Base rate" required />
      <input name="accessorials" placeholder="Accessorials" />
      <button><CircleDollarSign size={15} /> Confirm</button>
    </form>
  );
}

function PodUploadForm({ load, mutate }: { load: Load; mutate: AppMutate }) {
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    await mutate('POD uploaded', () => api.post(`/pod/${load.id}`, data, { headers: { 'Content-Type': 'multipart/form-data' } }));
    form.reset();
  }
  return (
    <form className="inlineForm" onSubmit={submit}>
      <input name="file" type="file" required />
      <button><Upload size={15} /> Upload POD</button>
    </form>
  );
}

function PodLink({ pod }: { pod: NonNullable<Load['pod']> }) {
  const href = `${API_ROOT}/${pod.url}`.replace(/([^:]\/)\/+/g, '$1');
  return <a className="fileLink" href={href} target="_blank" rel="noreferrer"><FileCheck size={15} /> {pod.file_name}</a>;
}

function AuditViewer({ rows }: { rows: AuditRow[] }) {
  return (
    <section className="section">
      <div className="sectionHead">
        <h2><Clock size={17} /> Audit log</h2>
      </div>
      <div className="auditList">
        {rows.slice(0, 12).map((row) => (
          <div className="auditRow" key={row.id}>
            <strong>{row.action}</strong>
            <span>{row.entity_type || 'system'} {row.entity_id || ''}</span>
            <small>{new Date(row.created_at).toLocaleString()}</small>
          </div>
        ))}
        {!rows.length && <p className="muted">No audit entries visible for this account.</p>}
      </div>
    </section>
  );
}

function LoadDrawer({ load, user, mutate, onClose }: { load: Load; user: User; mutate: AppMutate; onClose: () => void }) {
  const [history, setHistory] = useState<HistoryRow[]>([]);
  const [audit, setAudit] = useState<AuditRow[]>([]);

  useEffect(() => {
    api.get(`/loads/${load.id}/history`).then((res) => setHistory(res.data)).catch(() => setHistory([]));
    api.get(`/loads/${load.id}/audit`).then((res) => setAudit(res.data)).catch(() => setAudit([]));
  }, [load.id]);

  return (
    <aside className="drawer">
      <button className="close" onClick={onClose}>x</button>
      <h2>{load.reference}</h2>
      <p className="lane">{load.origin} to {load.destination}</p>
      <dl>
        <dt>Status</dt><dd>{load.status}</dd>
        <dt>Shipper</dt><dd>{load.shipper}</dd>
        <dt>Carrier</dt><dd>{load.carrier || 'Unassigned'}</dd>
        <dt>Compliance</dt><dd>{load.compliance_flag ? load.compliance_reason : 'Clear'}</dd>
        <dt>Rate</dt><dd>{load.rate ? `$${load.rate.base_rate} v${load.rate.version}` : 'Not confirmed'}</dd>
        <dt>POD</dt><dd>{load.pod ? <PodLink pod={load.pod} /> : 'Not uploaded'}</dd>
      </dl>
      {load.status === 'Delivered' && user.permissions.includes('pod.upload') && <PodUploadForm load={load} mutate={mutate} />}
      <h3>Status history</h3>
      <div className="auditList compact">
        {history.map((row) => (
          <div className="auditRow" key={row.id}>
            <strong>{row.from_status || 'Start'} to {row.to_status}</strong>
            <span>{row.note || 'Status changed'}</span>
            <small>{new Date(row.created_at).toLocaleString()}</small>
          </div>
        ))}
      </div>
      <h3>Load audit</h3>
      <div className="auditList compact">
        {audit.map((row) => (
          <div className="auditRow" key={row.id}>
            <strong>{row.action}</strong>
            <small>{new Date(row.created_at).toLocaleString()}</small>
          </div>
        ))}
      </div>
    </aside>
  );
}

export default App;
