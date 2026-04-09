import { NextResponse } from 'next/server';

export async function GET() {
  const nodes = [
    {
      id: 'node-asia-1',
      region: 'Asia',
      status: Math.random() > 0.1 ? 'Healthy' : 'Busy',
      latency: Math.round(40 + Math.random() * 20),
      capacity: Math.round(70 + Math.random() * 30),
    },
    {
      id: 'node-asia-2',
      region: 'Asia',
      status: Math.random() > 0.1 ? 'Healthy' : 'Busy',
      latency: Math.round(45 + Math.random() * 25),
      capacity: Math.round(60 + Math.random() * 40),
    },
    {
      id: 'node-europe-1',
      region: 'Europe',
      status: Math.random() > 0.05 ? 'Healthy' : 'Down',
      latency: Math.round(20 + Math.random() * 20),
      capacity: Math.round(75 + Math.random() * 25),
    },
    {
      id: 'node-europe-2',
      region: 'Europe',
      status: Math.random() > 0.15 ? 'Healthy' : 'Busy',
      latency: Math.round(25 + Math.random() * 25),
      capacity: Math.round(80 + Math.random() * 20),
    },
    {
      id: 'node-america-1',
      region: 'America',
      status: Math.random() > 0.1 ? 'Healthy' : 'Busy',
      latency: Math.round(15 + Math.random() * 15),
      capacity: Math.round(65 + Math.random() * 35),
    },
    {
      id: 'node-america-2',
      region: 'America',
      status: Math.random() > 0.1 ? 'Healthy' : 'Busy',
      latency: Math.round(18 + Math.random() * 18),
      capacity: Math.round(60 + Math.random() * 40),
    },
  ];

  return NextResponse.json(nodes);
}
