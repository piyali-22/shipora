import { motion } from "framer-motion";

export default function AuthLayout({ children, eyebrow, title, subtitle }) {
  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-canvas">
      {/* Left — brand panel */}
      <div className="hidden lg:flex flex-col justify-between bg-ink px-12 py-10 relative overflow-hidden">
        <div className="absolute inset-0 opacity-[0.07]" aria-hidden>
          <RouteMap />
        </div>

        <div className="relative flex items-center gap-2.5">
          <img src="/shipora-icon.svg" alt="" className="w-8 h-8" />
          <span className="text-white font-bold text-lg tracking-tight">SHIPORA</span>
        </div>

        <div className="relative">
          <motion.p
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-3xl font-bold text-white leading-tight max-w-md"
          >
            Every shipment, tracked from the first mile to the last.
          </motion.p>
          <p className="mt-4 text-slate-400 text-sm max-w-sm">
            Smart last-mile logistics for teams who need reliable pricing, intelligent dispatch, and a tracking
            history that never lies.
          </p>
        </div>

        <div className="relative flex items-center gap-6 text-xs text-slate-500 font-mono">
          <span>ZONE-AWARE PRICING</span>
          <span>·</span>
          <span>LIVE DISPATCH</span>
          <span>·</span>
          <span>IMMUTABLE TRACKING</span>
        </div>
      </div>

      {/* Right — form */}
      <div className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <img src="/shipora-icon.svg" alt="" className="w-7 h-7" />
            <span className="font-bold text-ink tracking-tight">SHIPORA</span>
          </div>

          {eyebrow && (
            <span className="text-xs font-semibold uppercase tracking-wide text-brand-600">{eyebrow}</span>
          )}
          <h1 className="mt-1 text-2xl font-bold text-ink">{title}</h1>
          {subtitle && <p className="mt-1.5 text-sm text-ink-muted">{subtitle}</p>}

          <div className="mt-8">{children}</div>
        </div>
      </div>
    </div>
  );
}

// A quiet abstract route line pattern — the visual signature, echoing
// the tracking-timeline idea without literally drawing a timeline.
function RouteMap() {
  return (
    <svg viewBox="0 0 600 800" className="w-full h-full" preserveAspectRatio="xMidYMid slice">
      <path
        d="M-20 100 Q 150 50 200 200 T 400 350 Q 500 400 480 550 T 620 700"
        stroke="white"
        strokeWidth="1.5"
        fill="none"
      />
      <path
        d="M-40 400 Q 100 380 180 500 T 350 600 Q 450 620 500 750"
        stroke="white"
        strokeWidth="1"
        fill="none"
      />
      <circle cx="200" cy="200" r="3" fill="white" />
      <circle cx="400" cy="350" r="3" fill="white" />
      <circle cx="480" cy="550" r="3" fill="white" />
    </svg>
  );
}
