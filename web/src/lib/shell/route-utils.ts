export function isRouteActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function isSafeInternalHref(href: string): boolean {
  return (
    href.startsWith("/") &&
    !href.startsWith("//") &&
    !href.includes("\\")
  );
}
