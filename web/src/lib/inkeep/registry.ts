export interface SiteConfig {
  url: string;
  description: string;
}

export const DEFAULT_SITES: Record<string, SiteConfig> = {
  langfuse: {
    url: "https://langfuse.com",
    description: "Langfuse (LLM Engineering Platform) official documentation"
  },
  render: {
    url: "https://render.com/docs",
    description: "Render (Cloud Hosting) official documentation"
  },
  clerk: {
    url: "https://clerk.com/docs",
    description: "Clerk (Authentication) official documentation"
  },
  neon: {
    url: "https://neon.com/docs",
    description: "Neon (Serverless Postgres) official documentation"
  },
  teleport: {
    url: "https://goteleport.com/docs",
    description: "Teleport (Access Plane) official documentation"
  },
  react: {
    url: "https://react.dev",
    description: "The library for web and native user interfaces."
  },
  bootstrap: {
    url: "https://getbootstrap.com",
    description: "The most popular HTML, CSS, and JavaScript framework for dev"
  },
  ragflow: {
    url: "https://ragflow.io",
    description: "RAGFlow is a leading open-source Retrieval-Augmented Generat"
  },
  node: {
    url: "https://base.org",
    description: "Everything required to run your own Base node"
  },
  "socket-io": {
    url: "https://socket.io",
    description: "Realtime application framework (Node.JS server)"
  },
  sway: {
    url: "https://docs.fuel.network/docs/sway",
    description: "🌴 Empowering everyone to build reliable and efficient smart "
  },
  bun: {
    url: "https://bun.com",
    description: "Incredibly fast JavaScript runtime, bundler, test runner, and package manager."
  },
  zod: {
    url: "https://zod.dev",
    description: "TypeScript-first schema validation with static type inference."
  },
  novu: {
    url: "https://docs.novu.co",
    description: "The open-source notification Inbox infrastructure. E-mail, SMS, and Push."
  },
  litellm: {
    url: "https://docs.litellm.ai/docs",
    description: "Python SDK, Proxy Server (AI Gateway) to call 100+ LLM APIs."
  },
  posthog: {
    url: "https://posthog.com",
    description: "🦔 PostHog is an all-in-one developer platform for building products."
  },
  goose: {
    url: "https://block.github.io/goose",
    description: "An open source, extensible AI agent that goes beyond code suggestions."
  },
  frigate: {
    url: "https://docs.frigate.video",
    description: "NVR with realtime local object detection for IP cameras."
  },
  fingerprintjs: {
    url: "https://docs.fingerprint.com",
    description: "The most advanced free and open-source browser fingerprinting."
  },
  spacetimedb: {
    url: "https://spacetimedb.com/docs",
    description: "Multiplayer at the speed of light."
  },
  nextra: {
    url: "https://nextra.site",
    description: "Simple, powerful and flexible site generation framework with Next.js."
  },
  zitadel: {
    url: "https://zitadel.com",
    description: "ZITADEL - Identity infrastructure, simplified for you."
  }
};
