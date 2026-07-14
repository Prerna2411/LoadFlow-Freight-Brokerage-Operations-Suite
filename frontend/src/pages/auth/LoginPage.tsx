import type { FormEvent } from 'react';

export function LoginPage({ onSubmit }: { onSubmit: (email: string, password: string) => void }) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    onSubmit(String(data.email), String(data.password));
  }

  return (
    <form className="manualLogin" onSubmit={submit}>
      <input name="email" type="email" placeholder="Email" required />
      <input name="password" type="password" placeholder="Password" required />
      <button>Sign in</button>
    </form>
  );
}
