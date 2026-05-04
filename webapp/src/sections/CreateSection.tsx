import { useState } from "react";
import { Audience, Occasion, Style, Step, OrderRequest, OrderResponse } from "@/types";
import { SongDraft, OrderInfo } from "@/App";
import { AUDIENCES, OCCASIONS, STYLES } from "@/lib/songcraft-data";
import { api } from "@/hooks/useApi";

interface Props {
  draft: SongDraft;
  onDraftChange: (d: SongDraft) => void;
  onBack: () => void;
  onOrderCreated: (order: OrderInfo) => void;
}

export function CreateSection({ draft, onDraftChange, onBack, onOrderCreated }: Props) {
  const [step, setStep] = useState<Step>(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const canNext = () => {
    if (step === 1) return !!draft.audience;
    if (step === 2) return !!draft.occasion;
    return !!draft.style;
  };

  const update = (patch: Partial<SongDraft>) => onDraftChange({ ...draft, ...patch });

  const handleSubmit = async () => {
    setSubmitting(true);
    setError("");
    try {
      const req: OrderRequest = {
        audience: draft.audience as Audience,
        occasion: draft.occasion as Occasion,
        personal_note: draft.personalNote,
        style: draft.style as Style,
        language: "zh",
        tier: draft.tier,
      };
      const resp = await api.createOrder(req);
      // MVP: trigger generation immediately
      await api.triggerGenerate(resp.order_id);
      onOrderCreated({
        orderId: resp.order_id,
        price: resp.price,
        tier: draft.tier,
      });
    } catch (e: any) {
      setError(e.message || "网络错误，请重试");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col min-h-full pt-8 pb-8">
      {/* Progress indicator */}
      <div className="flex items-center justify-center mb-12 px-6">
        {([1, 2, 3] as Step[]).map((s, i) => (
          <div key={s} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                  step === s
                    ? "bg-[#e94560] text-white"
                    : step > s
                    ? "bg-[#0f3460] text-white"
                    : "bg-white/[0.06] text-muted-foreground"
                }`}
              >
                {s}
              </div>
              <span
                className={`text-xs mt-1.5 ${
                  step >= s ? "text-muted-foreground" : "text-muted-foreground/40"
                }`}
              >
                {["听众", "心情", "风格"][i]}
              </span>
            </div>
            {s < 3 && (
              <div
                className={`w-12 h-px mb-5 mx-2 ${
                  step > s ? "bg-[#0f3460]" : "bg-white/[0.06]"
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step 1 — Audience */}
      {step === 1 && (
        <div className="flex-1 space-y-8">
          <h2 className="text-3xl font-medium">这首歌是给谁的？</h2>
          <div className="grid grid-cols-2 gap-4">
            {AUDIENCES.map((a) => (
              <button
                key={a.key}
                onClick={() => update({ audience: a.key })}
                className={`flex flex-col items-center rounded-xl border py-8 px-4 transition-all ${
                  draft.audience === a.key
                    ? "border-[#e94560] bg-[#e94560]/10"
                    : "border-white/[0.06] bg-white/[0.03] hover:border-white/[0.12]"
                }`}
              >
                <span className="text-4xl mb-3">{a.icon}</span>
                <span className="text-lg font-medium">{a.label}</span>
                <span className="text-xs text-muted-foreground mt-1">{a.hint}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 2 — Occasion */}
      {step === 2 && (
        <div className="flex-1 space-y-8">
          <h2 className="text-3xl font-medium">这首歌用在什么场合？</h2>
          <div className="flex flex-col gap-2.5">
            {OCCASIONS.map((o) => (
              <button
                key={o.key}
                onClick={() => update({ occasion: o.key })}
                className={`text-left rounded-xl border py-4 px-5 text-lg transition-all ${
                  draft.occasion === o.key
                    ? "border-[#e94560] bg-[#e94560]/10"
                    : "border-white/[0.06] bg-white/[0.03] hover:border-white/[0.12]"
                }`}
              >
                {o.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 3 — Style + personal note */}
      {step === 3 && (
        <div className="flex-1 space-y-8">
          <div className="space-y-4">
            <h2 className="text-3xl font-medium">选一个风格</h2>
            <div className="flex flex-wrap gap-3">
              {STYLES.map((s) => (
                <button
                  key={s.key}
                  onClick={() => update({ style: s.key })}
                  className={`px-5 py-2.5 rounded-full border text-base transition-all ${
                    draft.style === s.key
                      ? "border-[#e94560] bg-[#e94560]/15 text-[#e94560]"
                      : "border-white/[0.08] bg-white/[0.03] hover:border-white/[0.15]"
                  }`}
                >
                  {s.name}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <h2 className="text-3xl font-medium">有什么特别的话想加进去？</h2>
            <p className="text-sm text-muted-foreground">
              比如TA的喜好、你们的回忆、特定的地名或人名（选填）
            </p>
            <textarea
              value={draft.personalNote}
              onChange={(e) => update({ personalNote: e.target.value })}
              placeholder="比如：她喜欢向日葵，我们在贵州认识的..."
              maxLength={200}
              className="w-full h-36 bg-white/[0.04] border border-white/[0.08] rounded-xl p-4 text-base text-white placeholder:text-muted-foreground/50 resize-none outline-none focus:border-[#e94560]/50"
            />
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Navigation */}
      <div className="flex gap-3 mt-8">
        {step > 1 ? (
          <button
            onClick={() => setStep((s) => (s - 1) as Step)}
            className="flex-1 py-3.5 rounded-full border border-white/[0.1] text-muted-foreground font-medium text-lg hover:bg-white/[0.04] transition-all"
          >
            上一步
          </button>
        ) : (
          <button
            onClick={onBack}
            className="flex-1 py-3.5 rounded-full border border-white/[0.1] text-muted-foreground font-medium text-lg hover:bg-white/[0.04] transition-all"
          >
            返回
          </button>
        )}

        {step < 3 ? (
          <button
            onClick={() => setStep((s) => (s + 1) as Step)}
            disabled={!canNext()}
            className="flex-1 py-3.5 rounded-full bg-[#e94560] hover:bg-[#d63850] active:scale-[0.98] disabled:opacity-40 text-white font-medium text-lg transition-all"
          >
            下一步
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!canNext() || submitting}
            className="flex-1 py-3.5 rounded-full bg-[#e94560] hover:bg-[#d63850] active:scale-[0.98] disabled:opacity-40 text-white font-medium text-lg transition-all"
          >
            {submitting ? "创建中..." : `确认，付¥${draft.tier === "premium" ? "8" : "5"}`}
          </button>
        )}
      </div>
    </div>
  );
}
