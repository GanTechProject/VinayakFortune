"""Public API surface — FastAPI REST + gRPC control surface.

Per Architect #6 §7 (Doc 02 §4.2 L189-191):
- gRPC: synchronous control surface (StartRun, GetRun, CancelRun)
- NATS: event surface (CloudEvents v1.0 envelopes)
- REST (FastAPI): HTTP API for the public surface
"""
