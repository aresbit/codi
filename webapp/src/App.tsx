import { Component, ReactNode, useState, useEffect } from "react";
import type { Audience, Language, Occasion, Style, OrderStatus } from "@/types";
import { api } from "@/hooks/useApi";
import { AUDIENCES, LANGUAGES, OCCASIONS, STYLES } from "@/lib/codi-data";

// ── Error Boundary ──
class ErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(e: Error) {
    return { error: e };
  }
  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen bg-[#1a1a2e] text-white flex flex-col items-center justify-center p-8 gap-4">
          <span className="text-6xl">💥</span>
          <h2 className="text-2xl font-medium">应用出错了</h2>
          <pre className="text-sm text-red-400 bg-white/5 rounded-xl p-4 max-w-full overflow-auto">
            {this.state.error.message}
          </pre>
          <button
            onClick={() => window.location.reload()}
            className="px-8 py-3 rounded-full bg-[#e94560] text-white font-medium"
          >
            重新加载
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// ── Data types ──
interface SongDraft {
  language: Language;
  audience: Audience | "";
  occasion: Occasion | "";
  personalNote: string;
  style: Style | "";
  generateVideo: boolean;
  exactLyrics: string;
}

interface OrderInfo {
  orderId: string;
}

type Page = "home" | "create" | "result";

type Step = 1 | 2 | 3;

const initialDraft: SongDraft = {
  language: "zh",
  audience: "",
  occasion: "",
  personalNote: "",
  style: "",
  generateVideo: false,
  exactLyrics: "",
};

// ── App ──
export default function App() {
  const [page, setPage] = useState<Page>("home");
  const [draft, setDraft] = useState<SongDraft>(initialDraft);
  const [order, setOrder] = useState<OrderInfo | null>(null);

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#1a1a2e] via-[#16213e] to-[#0f3460] text-white">
      <div className="mx-auto max-w-md min-h-screen p-4 flex flex-col">
        <ErrorBoundary>
          {page === "home" && (
            <HomePage onStart={() => setPage("create")} />
          )}
          {page === "create" && (
            <CreatePage
              draft={draft}
              onDraftChange={setDraft}
              onBack={() => setPage("home")}
              onOrderCreated={(o) => {
                setOrder(o);
                setPage("result");
              }}
            />
          )}
          {page === "result" && order && (
            <ResultPage
              order={order}
              onNewSong={() => {
                setDraft(initialDraft);
                setOrder(null);
                setPage("home");
              }}
            />
          )}
        </ErrorBoundary>
      </div>
    </div>
  );
}

// ── Home Page ──
function HomePage({ onStart }: { onStart: () => void }) {
  return (
    <div className="flex flex-col items-center pt-16 pb-8 gap-8">
      <div className="text-center space-y-4">
        <div className="text-7xl">🎵</div>
        <h1 className="text-4xl font-medium tracking-wider">用AI为ta写一首歌</h1>
        <p className="text-base text-muted-foreground leading-relaxed">
          选风格 · 说心情
          <br />
          几分钟拿到属于你们的歌
        </p>
      </div>

      <div className="bg-white/5 border border-white/[0.06] rounded-xl px-8 py-5 text-center text-sm text-muted-foreground space-y-1">
        <p>今天有人为他们的婚礼</p>
        <p>创作了一首中国风歌曲</p>
        <p>💍</p>
      </div>

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

      <button
        onClick={onStart}
        className="w-full py-3.5 rounded-full bg-[#e94560] hover:bg-[#d63850] active:scale-[0.98] text-white font-medium text-lg transition-all"
      >
        开始定制
      </button>
    </div>
  );
}

// ── Create Page ──
function CreatePage({
  draft,
  onDraftChange,
  onBack,
  onOrderCreated,
}: {
  draft: SongDraft;
  onDraftChange: (d: SongDraft) => void;
  onBack: () => void;
  onOrderCreated: (order: OrderInfo) => void;
}) {
  const [step, setStep] = useState<Step>(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const canNext = () => {
    if (step === 1) return !!draft.audience;
    if (step === 2) return !!draft.occasion;
    return !!draft.style;
  };

  const update = (patch: Partial<SongDraft>) =>
    onDraftChange({ ...draft, ...patch });

  const handleSubmit = async () => {
    setSubmitting(true);
    setError("");
    try {
      const req = {
        audience: draft.audience as Audience,
        occasion: draft.occasion as Occasion,
        personal_note: draft.personalNote,
        style: draft.style as Style,
        language: draft.language,
        generate_video: draft.generateVideo,
        exact_lyrics: draft.exactLyrics,
      };
      const resp = await api.createOrder(req);
      onOrderCreated({ orderId: resp.order_id });
    } catch (e: any) {
      setError(e.message || "网络错误，请重试");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col min-h-full pt-8 pb-8">
      {/* Steps indicator */}
      <div className="flex items-center justify-center mb-12">
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
                className={`text-xs mt-1.5 ${step >= s ? "text-muted-foreground" : "text-muted-foreground/40"}`}
              >
                {["听众", "心情", "风格"][i]}
              </span>
            </div>
            {s < 3 && (
              <div
                className={`w-12 h-px mb-5 mx-2 ${step > s ? "bg-[#0f3460]" : "bg-white/[0.06]"}`}
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

          <div className="space-y-4">
            <h2 className="text-3xl font-medium">选择语言</h2>
            <div className="flex flex-wrap gap-3">
              {LANGUAGES.map((l) => (
                <button
                  key={l.key}
                  onClick={() => update({ language: l.key })}
                  className={`px-4 py-2 rounded-full border text-sm transition-all ${
                    draft.language === l.key
                      ? "border-[#e94560] bg-[#e94560]/15 text-[#e94560]"
                      : "border-white/[0.08] bg-white/[0.03] hover:border-white/[0.15]"
                  }`}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>

          {/* 视频生成开关 */}
          <div className="flex items-center justify-between rounded-xl border border-white/[0.08] bg-white/[0.03] px-5 py-4">
            <div>
              <p className="text-base font-medium">生成视频（MP4）</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                勾选后会合成视频，耗时较长
              </p>
            </div>
            <button
              onClick={() => update({ generateVideo: !draft.generateVideo })}
              className={`w-14 h-7 rounded-full transition-all ${
                draft.generateVideo
                  ? "bg-[#e94560]"
                  : "bg-white/[0.12]"
              }`}
            >
              <div
                className={`w-5 h-5 rounded-full bg-white transition-all ${
                  draft.generateVideo ? "translate-x-8" : "translate-x-1.5"
                }`}
              />
            </button>
          </div>

          <div className="space-y-3">
            <h2 className="text-3xl font-medium">有什么特别的话想加进去？</h2>
            <p className="text-sm text-muted-foreground">
              比如TA的喜好、你们的回忆、特定的地名或人名（选填）
            </p>
            <textarea
              value={draft.personalNote}
              onChange={(e) => update({ personalNote: e.target.value })}
              placeholder="比如：她喜欢向日葵，我们在苏州认识的..."
              maxLength={2000}
              className="w-full h-28 bg-white/[0.04] border border-white/[0.08] rounded-xl p-4 text-base text-white placeholder:text-muted-foreground/50 resize-none outline-none focus:border-[#e94560]/50"
            />
          </div>

          {/* 精确歌词输入 */}
          <div className="space-y-3">
            <h2 className="text-3xl font-medium">填写歌词（可选）</h2>
            <p className="text-sm text-muted-foreground">
              填写后 AI 将使用你提供的歌词，不会修改。留空则由 AI 自动创作
            </p>
            <textarea
              value={draft.exactLyrics}
              onChange={(e) => update({ exactLyrics: e.target.value })}
              placeholder={"[VERSE 1]\n你的歌词第一段...\n\n[CHORUS]\n你的副歌歌词...\n\n[VERSE 2]\n你的歌词第二段..."}
              maxLength={10000}
              className="w-full h-48 bg-white/[0.04] border border-white/[0.08] rounded-xl p-4 text-base text-white placeholder:text-muted-foreground/50 resize-none outline-none focus:border-[#e94560]/50 font-mono text-sm"
            />
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-sm text-red-400 mt-4">
          {error}
        </div>
      )}

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
            {submitting ? "创作中..." : "开始创作"}
          </button>
        )}
      </div>
    </div>
  );
}

// ── Result Page ──
function ResultPage({
  order,
  onNewSong,
}: {
  order: OrderInfo;
  onNewSong: () => void;
}) {
  const [status, setStatus] = useState<OrderStatus>("generating");
  const [lyrics, setLyrics] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [audioUrl, setAudioUrl] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const elapsedTimer = setInterval(
      () => setElapsed((e) => e + 1),
      1000,
    );

    const pollTimer = setInterval(async () => {
      try {
        const data = await api.getOrderStatus(order.orderId);
        if (data.status === "completed") {
          clearInterval(pollTimer);
          clearInterval(elapsedTimer);
          setStatus("completed");
          setLyrics(data.lyrics || "");

          const fileId = order.orderId;
          if (data.audio_url) {
            const parts = data.audio_url.split("/");
            setAudioUrl(api.getFileUrl(fileId, parts[parts.length - 1]));
          }
          if (data.video_url) {
            const parts = data.video_url.split("/");
            setVideoUrl(api.getFileUrl(fileId, parts[parts.length - 1]));
          }
        } else if (data.status === "failed") {
          clearInterval(pollTimer);
          clearInterval(elapsedTimer);
          setStatus("failed");
          setErrorMsg(data.error_message || "未知错误");
        }
      } catch {
        // keep polling
      }
    }, 2000);

    return () => {
      clearInterval(pollTimer);
      clearInterval(elapsedTimer);
    };
  }, [order.orderId]);

  if (status === "generating" || status === "pending") {
    return (
      <div className="flex flex-col items-center justify-center flex-1 gap-6 pt-32">
        <div className="w-20 h-20 border-4 border-white/[0.06] border-t-[#e94560] rounded-full animate-spin" />
        <h2 className="text-2xl font-medium">正在为你创作...</h2>
        <p className="text-sm text-muted-foreground">AI正在谱写旋律、编排歌词</p>
        <p className="text-xs text-muted-foreground/60">已等待 {elapsed} 秒</p>
      </div>
    );
  }

  if (status === "failed") {
    return (
      <div className="flex flex-col items-center justify-center flex-1 gap-6 pt-32">
        <span className="text-7xl">😟</span>
        <h2 className="text-2xl font-medium">生成失败</h2>
        <p className="text-sm text-muted-foreground text-center">{errorMsg}</p>
        <button
          onClick={() => window.location.reload()}
          className="w-full py-3.5 rounded-full bg-[#e94560] hover:bg-[#d63850] text-white font-medium text-lg transition-all"
        >
          重新生成
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8 py-8">
      <div className="text-center space-y-2">
        <span className="text-7xl">✨</span>
        <h2 className="text-3xl font-medium">你的歌已经创作完成</h2>
      </div>

      {videoUrl ? (
        <div className="rounded-2xl overflow-hidden border border-white/[0.06] bg-black/30">
          <video
            src={videoUrl}
            controls
            className="w-full aspect-[9/16] object-cover"
          />
        </div>
      ) : audioUrl ? (
        <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] px-5 py-6">
          <audio
            src={audioUrl}
            controls
            className="w-full"
            style={{ height: 48 }}
          />
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-white/[0.06] bg-white/[0.02] aspect-[9/16] gap-4">
          <span className="text-5xl">🎵</span>
          <span className="text-sm text-muted-foreground">点击播放</span>
        </div>
      )}

      {lyrics && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-5 max-h-60 overflow-y-auto">
          <p className="text-xs text-muted-foreground mb-3">歌词预览</p>
          <p className="text-base leading-relaxed whitespace-pre-wrap">
            {lyrics}
          </p>
        </div>
      )}

      <div className="flex flex-col gap-3">
        {audioUrl && (
          <a
            href={audioUrl}
            download
            className="w-full py-3.5 rounded-full bg-[#e94560] hover:bg-[#d63850] text-white font-medium text-lg text-center transition-all"
          >
            下载 MP3 音频
          </a>
        )}
        {videoUrl && (
          <a
            href={videoUrl}
            download
            className="w-full py-3.5 rounded-full border border-white/[0.1] text-muted-foreground hover:bg-white/[0.04] font-medium text-lg text-center transition-all"
          >
            下载 MP4 视频
          </a>
        )}
        {lyrics && (
          <a
            onClick={(e) => {
              const blob = new Blob([lyrics], { type: 'text/plain;charset=utf-8' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `${order.orderId}-lyrics.txt`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            className="w-full py-3.5 rounded-full border border-white/[0.1] text-muted-foreground hover:bg-white/[0.04] font-medium text-lg text-center transition-all"
          >
            下载歌词（TXT）
          </a>
        )}
        <button
          onClick={() => {
            if (navigator.share) {
              navigator.share({
                title: "我用AI定制了一首歌",
                text: "用Codi为你的ta写一首歌吧",
              });
            }
          }}
          className="w-full py-3.5 rounded-full border border-white/[0.1] text-muted-foreground hover:bg-white/[0.04] font-medium text-lg transition-all"
        >
          分享给朋友
        </button>
        <button
          onClick={onNewSong}
          className="w-full py-3.5 rounded-full border border-white/[0.06] text-muted-foreground/60 hover:bg-white/[0.04] font-medium text-lg transition-all"
        >
          再创作一首
        </button>
      </div>
    </div>
  );
}
