import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { file } = body;

    if (!file) {
      return NextResponse.json({ error: 'Missing file parameter' }, { status: 400 });
    }

    // Simulate purge operation
    await new Promise((resolve) => setTimeout(resolve, Math.random() * 300 + 100));

    return NextResponse.json({
      success: true,
      message: `File "${file}" purged from all edge nodes`,
      purgedAt: new Date().toISOString(),
    });
  } catch (error) {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
  }
}
