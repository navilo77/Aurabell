import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

function decodeRole(token: string | undefined): string | null {
  if (!token) return null;
  try {
    const payload = token.split(".")[1];
    const json = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
    return (json.role as string) ?? null;
  } catch {
    return null;
  }
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("aura_access_token")?.value;
  const role = decodeRole(token);

  const isProtected =
    pathname.startsWith("/account") ||
    pathname.startsWith("/store-admin") ||
    pathname.startsWith("/super-admin") ||
    pathname.startsWith("/shop/cart");

  if (isProtected && !token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (pathname === "/login" && token) {
    return NextResponse.redirect(new URL("/shop", request.url));
  }

  if (pathname.startsWith("/store-admin") && role !== "store_manager") {
    return NextResponse.redirect(new URL("/shop", request.url));
  }

  if (pathname.startsWith("/super-admin") && !["owner", "admin", "super_admin"].includes(role ?? "")) {
    return NextResponse.redirect(new URL("/shop", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next|.*\\..*).*)"],
};