import { Tier } from "@/types";
import { SongDraft } from "@/App";
import { STYLES } from "@/lib/songcraft-data";

interface Props {
  draft: SongDraft;
  onDraftChange: (d: SongDraft) => void;
  onStart: () => void;
}

export function HomeSection({ draft, onDraftChange, onStart }: Props) {
  return (
    <div className="flex flex-col items-center pt-16 pb-8 gap-8">
      {/* Hero */}
      <div className="text-center space-y-4">
        <div className="text-7xl">🎵</div>
        <h1 className="text-4xl font-medium tracking-wider">用AI为ta写一首歌</h1>
        <p className="text-base text-muted-foreground leading-relaxed">
          选风格 · 说心情 · 扫码付
          <br />
          几分钟拿到属于你们的歌
        </p>
      </div>

      {/* Demo hint */}
      <div className="bg-white/5 border border-white/[0.06] rounded-xl px-8 py-5 text-center text-sm text-muted-foreground space-y-1">
        <p>今天有人为他们的婚礼</p>
        <p>创作了一首中国风歌曲</p>
        <p>💍</p>
      </div>

      {/* Pricing cards */}
      <div className="w-full flex gap-4 px-2">
        <TierCard
          name="基础版"
          price={5}
          desc="MP4 · 带歌词"
          active={draft.tier === "basic"}
          onClick={() => onDraftChange({ ...draft, tier: "basic" })}
        />
        <TierCard
          name="完整版"
          price={8}
          desc="MP4 · 歌词 · 曲谱"
          active={draft.tier === "premium"}
          onClick={() => onDraftChange({ ...draft, tier: "premium" })}
          recommended
        />
      </div>

      {/* Style preview */}
      <div className="w-full space-y-3">
        <p className="text-xs text-muted-foreground pl-1">可选风格</p>
        <div className="flex flex-wrap gap-2.5">
          {STYLES.map((s) => (
            <span
              key={s.key}
              className="inline-flex items-center px-4 py-2 text-sm rounded-full border border-white/[0.1] bg-white/[0.04] text-muted-foreground"
            >
              {s.name}
            </span>
          ))}
        </div>
      </div>

      {/* CTA */}
      <button
        onClick={onStart}
        className="w-full py-3.5 rounded-full bg-[#e94560] hover:bg-[#d63850] active:scale-[0.98] text-white font-medium text-lg transition-all"
      >
        开始定制
      </button>
    </div>
  );
}

function TierCard({
  name, price, desc, active, onClick, recommended,
}: {
  name: string; price: number; desc: string;
  active: boolean; onClick: () => void; recommended?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={`relative flex-1 flex flex-col items-center rounded-2xl border py-7 px-4 transition-all ${
        active
          ? "border-[#e94560] bg-[#e94560]/10"
          : "border-white/[0.08] bg-white/[0.02] hover:border-white/[0.15]"
      }`}
    >
      {recommended && (
        <span className="absolute -top-2.5 bg-[#e94560] text-white text-xs px-2.5 py-0.5 rounded-full">
          推荐
        </span>
      )}
      <span className="text-4xl font-medium">¥{price}</span>
      <span className="text-sm font-medium mt-1.5">{name}</span>
      <span className="text-xs text-muted-foreground mt-1">{desc}</span>
    </button>
  );
}
