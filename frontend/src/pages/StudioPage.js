import React from 'react';
import Navbar from '../components/layout/Navbar';

export default function StudioPage() {
  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#f8faff',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Navbar />
      <div
        style={{
          flex: '1 1 auto',
          minHeight: '0',
          height: 'calc(100dvh - 72px)',
          overflow: 'hidden',
        }}
      >
        <iframe
          src="/studio-app/index.html"
          title="CadArena Studio"
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            display: 'block',
          }}
          allow="clipboard-write"
        />
      </div>
    </div>
  );
}
