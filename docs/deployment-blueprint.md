# Project Elysia Deployment Blueprint

This document turns the current local MVP into a production-minded self-hosted deployment plan using:

- `Raspberry Pi` as the public entry point
- `GPU PC` as the private inference worker
- `Cloudflare Tunnel` for free public access

It is designed for the current architecture:

- Unity client over WebSocket
- Python backend relay in `Backend/core/elysia_server.py`
- `faster-whisper` for STT
- `GPT-SoVITS` for TTS
- streaming PCM audio back to the client

## 1. Short Answer: Do We Still Need Nginx on the Pi?

No, `Nginx` is not strictly required if you use `Cloudflare Tunnel`.

Cloudflare Tunnel can point directly to one local service on the Pi. That means this can work:

`Internet -> Cloudflare -> cloudflared on Pi -> gateway app on Pi`

However, I still recommend using `Nginx` or `Caddy` on the Pi because it gives you a cleaner public edge:

- serve the website or WebGL build
- route `/api` and `/ws`
- terminate and normalize headers cleanly
- keep one stable local upstream even if app ports change
- add simple rate limiting and request size limits
- make future expansion easier

Recommended rule:

- `Single service quick test`: Cloudflare Tunnel can point directly to the app
- `Public deployment you want to grow`: keep `Nginx` or `Caddy` on the Pi

For this project, the recommended setup is:

`Internet -> Cloudflare Tunnel -> Nginx/Caddy on Pi -> Pi gateway service -> GPU PC worker`

## 2. What "Website Access" Means for This Repo

Right now this repo is primarily a `Unity client + Python backend` project, not yet a normal browser-first web app.

So a public website link is possible, but you should choose one of these paths:

1. `Unity WebGL client`
2. `New browser frontend later`

The fastest path that stays close to the current project is `Unity WebGL`, but there is one immediate blocker in the current client:

- [Frontend/Assets/Script/ConnectionManager.cs](file:///c:/Users/Yau/Documents/YauProject/Project-Elysia/Frontend/Assets/Script/ConnectionManager.cs) currently hardcodes `ws://localhost:8765`

For a public deployment, that must become configurable and use the public endpoint, typically:

- local dev: `ws://localhost:8765`
- public: `wss://your-domain/ws`

## 3. Recommended Target Topology

```text
Browser / Unity WebGL / Unity client
        |
        v
Cloudflare
        |
        v
cloudflared on Raspberry Pi
        |
        v
Nginx or Caddy on Raspberry Pi
        |
        +--> static frontend / WebGL files
        |
        +--> /ws and /api -> Pi gateway service
                               |
                               v
                    private LAN or Tailscale
                               |
                               v
                        GPU PC inference worker
                        - faster-whisper
                        - GPT-SoVITS
                        - optional LLM relay
```

## 4. Node Responsibilities

### Raspberry Pi

The Pi should run only lightweight, public-facing components:

- `cloudflared`
- `Nginx` or `Caddy`
- static website or Unity WebGL build
- lightweight gateway/orchestrator service
- auth and session validation
- rate limiting
- health checks
- logging

The Pi should **not** run:

- `faster-whisper` inference
- `GPT-SoVITS` inference
- large model hosting

### GPU PC

The PC should remain the private worker machine:

- speech-to-text with `faster-whisper`
- text-to-speech with `GPT-SoVITS`
- model loading and warm state
- optional LLM access wrapper if you want one internal API boundary

The PC should not be exposed directly to the public internet.

## 5. Recommended Service Split

Your current backend in [Backend/core/elysia_server.py](file:///c:/Users/Yau/Documents/YauProject/Project-Elysia/Backend/core/elysia_server.py) is a single local WebSocket server that does everything.

Production-minded deployment should split it into two roles.

### Pi gateway service

Responsibilities:

- accept browser or Unity client connections
- validate auth/session
- enforce payload limits
- assign request IDs
- forward STT/TTS/chat work to the worker
- relay streaming responses back to the client

Suggested public-facing routes:

- `GET /health`
- `GET /ready`
- `POST /api/session`
- `WS /ws`

### GPU worker service

Responsibilities:

- transcribe audio
- call LLM if needed
- generate TTS
- stream PCM chunks back to the gateway

Suggested private routes:

- `GET /health`
- `POST /transcribe`
- `POST /chat`
- `POST /tts`
- `POST /pipeline`
- `WS /tts-stream` or `HTTP streaming /tts/stream`

## 6. Recommended Network Design

### Best free setup

- Pi and PC on the same home LAN
- Pi talks to PC using local IP, for example `192.168.1.20`
- only Pi is internet-facing through Cloudflare Tunnel

### If Pi and PC are not always on the same LAN

Use `Tailscale` between Pi and PC, then keep the same topology:

- public users -> Pi
- Pi -> PC over Tailscale private network

## 7. Why This Is the Right First Production Shape

This matches the current codebase and hardware constraints:

- streaming already exists
- STT and TTS are the heavy parts
- the Pi is good enough for routing and control
- the GPU PC stays hot with the loaded models
- you avoid public exposure of raw inference services

## 8. Deployment Stack

Recommended first stack:

- `Cloudflare Tunnel` on Pi
- `Nginx` or `Caddy` on Pi
- `systemd` or `Docker Compose` on Pi
- `systemd` or `Docker Compose` on PC
- Python gateway on Pi
- Python worker on PC

My preference for your stage is:

- `Caddy` if you want simpler config
- `Nginx` if you want the most familiar reverse proxy pattern

Either is fine.

## 9. Security Minimums

Before public access, add these controls.

### Required

- protect the public site with login or invite-only access
- add per-IP rate limits at the reverse proxy
- set max audio upload size
- set max recording duration
- add timeouts for upstream worker calls
- reject requests when the worker queue is full
- keep PC worker bound to private network only
- store secrets in `.env`, not in client code

### Strongly recommended

- request ID in every log line
- allowlist Pi -> PC worker calls
- basic abuse monitoring
- restart-on-failure service configs
- health and readiness endpoints

## 10. Reliability Minimums

To feel production-ish, the deployment needs these behaviors:

- automatic process restart
- startup order control
- worker warm-up on boot
- graceful handling when GPU worker is offline
- user-facing error message when the queue is full or worker is unavailable
- structured logs for every request

## 11. Concrete Config Blueprint

### Pi services

1. `cloudflared`
2. `nginx` or `caddy`
3. `elysia-gateway`
4. optional `fail2ban` later

### PC services

1. `elysia-worker`
2. `gpt-sovits`
3. optional local helper for LLM access

### Example logical ports

Pi:

- `127.0.0.1:8080` -> gateway app
- `127.0.0.1:8081` -> static frontend if separate

PC:

- `0.0.0.0:8765` -> internal worker WebSocket or API
- `127.0.0.1:9880` -> GPT-SoVITS if worker and GPT-SoVITS are on same PC

If the worker and GPT-SoVITS are both on the PC, keep GPT-SoVITS internal and let only the worker talk to it.

## 12. Current Code Changes Needed Before Public Launch

These are the most important repo-level changes implied by the deployment plan.

### Priority 1

- make the frontend WebSocket URL configurable instead of hardcoded `ws://localhost:8765`
- support `wss://` for public deployment
- separate gateway logic from inference logic in the backend

### Priority 2

- add request IDs and structured logging
- add health endpoints
- add payload size and timeout controls
- add worker busy or queue-full responses

### Priority 3

- add auth/session layer for the public website
- add rate limiting at the proxy
- add deployment configs such as `docker-compose.yml` or `systemd` units

## 13. Phased Rollout Plan

### Phase 0: Internal cleanup

Goal:

- remove localhost assumptions
- define gateway vs worker boundaries

Exit criteria:

- frontend can connect using configurable `ws` URL
- backend endpoints are documented

### Phase 1: LAN deployment

Goal:

- Pi and PC work together on the same home network

Exit criteria:

- Pi can reach PC reliably
- one full voice interaction succeeds through the Pi
- PCM streaming still works

### Phase 2: Public beta

Goal:

- expose a public link through Cloudflare Tunnel

Exit criteria:

- external user can open the site
- client connects over `wss`
- auth is enabled
- reverse proxy limits are active

### Phase 3: Hardening

Goal:

- improve stability and abuse resistance

Exit criteria:

- services auto-restart
- health checks exist
- logs are usable
- queue limits and timeouts exist

## 14. Deployment Decision Table

### Option A: Cloudflare Tunnel only, no Nginx

Use when:

- one app only
- quick prototype
- minimum moving parts

Pros:

- simplest path
- no router port forwarding

Cons:

- less flexible routing
- weaker separation between public edge and app

### Option B: Cloudflare Tunnel + Nginx/Caddy on Pi

Use when:

- you want a stable self-hosted public beta
- you may serve static files and WebSocket/API together

Pros:

- best balance for this project
- easier growth path
- cleaner edge controls

Cons:

- one more service to manage

### Option C: DDNS + port forwarding + Nginx/Caddy

Use when:

- you want direct exposure without Cloudflare Tunnel

Pros:

- full control

Cons:

- more router and security work
- higher exposure risk

## 15. Recommended Choice

For your current goal, use:

- `Cloudflare Tunnel + Nginx/Caddy on Raspberry Pi + private GPU PC worker`

That gives you:

- free public access
- no direct port forwarding
- private inference machine
- cleaner path toward a real public beta

## 16. First Implementation Milestone

The first milestone I would build toward is:

`One public URL -> one authenticated user -> one stable end-to-end voice conversation`

Success means:

- the site opens from outside your home network
- the client connects over `wss`
- the Pi relays requests to the PC
- `faster-whisper` and `GPT-SoVITS` stay on the PC
- the system survives disconnects and process restarts

## 17. Repo Follow-up Work

The next implementation sequence for this repo should be:

1. make WebSocket endpoint configurable in the frontend
2. split the backend into gateway and worker roles
3. add health endpoints and structured logs
4. add Pi proxy config and service definitions
5. add public auth and rate limiting

That is the point where the project moves from a local MVP to a self-hosted production-minded deployment.
