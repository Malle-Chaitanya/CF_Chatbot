import { NextRequest, NextResponse } from 'next/server';

const BACKEND_BASE =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8002';

function buildBackendUrl(token: string) {
  const base = BACKEND_BASE.replace(/\/$/, '');
  return `${base}/chat/shared/${token}`;
}

async function proxySharedChatRequest(token: string, request: NextRequest) {
  const backendUrl = buildBackendUrl(token);

  const headers = new Headers();
  headers.set('Accept', 'application/json');
  headers.set('Content-Type', 'application/json');

  const cookieHeader = request.headers.get('cookie');
  if (cookieHeader) {
    headers.set('Cookie', cookieHeader);
  }

  const backendResponse = await fetch(backendUrl, {
    method: 'GET',
    headers,
    credentials: 'include',
  });

  const responseText = await backendResponse.text();

  const response = new NextResponse(responseText, {
    status: backendResponse.status,
    headers: {
      'Content-Type': backendResponse.headers.get('content-type') || 'application/json',
    },
  });

  const setCookie = backendResponse.headers.get('set-cookie');
  if (setCookie) {
    response.headers.set('Set-Cookie', setCookie);
  }

  return response;
}

export async function GET(
  request: NextRequest,
  context: { params: { token: string } }
) {
  const token = context.params?.token;

  if (!token) {
    return NextResponse.json(
      { error: 'Missing share token' },
      { status: 400 }
    );
  }

  try {
    return await proxySharedChatRequest(token, request);
  } catch (error) {
    console.error('[API] Failed to proxy shared chat request:', error);
    return NextResponse.json(
      { error: 'Failed to proxy shared chat request' },
      { status: 502 }
    );
  }
}

