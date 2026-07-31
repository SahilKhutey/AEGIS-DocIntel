"""Security primitives: auth, RBAC/ABAC, rate limiting, audit, crypto.

All components are designed to be used by both:

  * the FastAPI HTTP surface (`amdi.api.middleware.*`)
  * the gRPC surface (`amdi.transport.grpc_interceptors.AuthServerInterceptor`)

via a single shared `JWTVerifier`.
"""
