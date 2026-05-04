import { useEffect, useState, useRef } from "react";
import { OrderStatus } from "@/types";
import { OrderInfo } from "@/App";
import { api } from "@/hooks/useApi";

interface Props {
  order: OrderInfo;
  onNewSong: () => void;
}

export function ResultSection({ order, onNewSong }: Props) {
  const [status, setStatus] = useState<OrderStatus>("generating");
  const [lyrics, setLyrics] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [sheetUrl, setSheetUrl] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval>>();
  const elapsedRef = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    // Start polling
    elapsedRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);

    timerRef.current = setInterval(async () => {
      try {
        const data = await api.getOrderStatus(order.orderId);
        if (data.status === "completed") {
          clearInterval(timerRef.current);
          clearInterval(elapsedRef.current);
          setStatus("completed");
          setLyrics(data.lyrics || "");
          if (data.video_url) setVideoUrl(api.getFileUrl(order.orderId, data.video_url.split("/").pop()!));
          if (data.sheet_music_url) setSheetUrl(api.getFileUrl(order.orderId, data.sheet_music_url.split("/").pop()!));
        } else if (data.status === "failed") {
          clearInterval(timerRef.current);
          clearInterval(elapsedRef.current);
          setStatus("failed");
          setErrorMsg(data.error_message || "未知错误");
        }
      } catch {
        // continue polling
      }
    }, 2000);

    return () => {
      clearInterval(timerRef.current);
      clearInterval(elapsedRef.current);
    };
  }, [order.orderId]);

  if (status === "generating" || status === "paid") {
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
      {/* Header */}
      <div className="text-center space-y-2">
        <span className="text-7xl">✨</span>
        <h2 className="text-3xl font-medium">你的歌已经创作完成</h2>
      </div>

      {/* Video preview */}
      {videoUrl ? (
        <div className="rounded-2xl overflow-hidden border border-white/[0.06] bg-black/30">
          <video
            src={videoUrl}
            controls
            className="w-full aspect-[9/16] object-cover"
            poster="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='700'><rect fill='%231a1a2e' width='400' height='700'/></svg>"
          />
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-white/[0.06] bg-white/[0.02] aspect-[9/16] gap-4">
          <span className="text-5xl">🎵</span>
          <span className="text-sm text-muted-foreground">点击播放</span>
        </div>
      )}

      {/* Lyrics */}
      {lyrics && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-5 max-h-60 overflow-y-auto">
          <p className="text-xs text-muted-foreground mb-3">歌词预览</p>
          <p className="text-base leading-relaxed whitespace-pre-wrap">{lyrics}</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-col gap-3">
        {videoUrl && (
          <a
            href={videoUrl}
            download
            className="w-full py-3.5 rounded-full bg-[#e94560] hover:bg-[#d63850] text-white font-medium text-lg text-center transition-all"
          >
            下载 MP4 视频
          </a>
        )}
        {sheetUrl && order.tier === "premium" && (
          <a
            href={sheetUrl}
            download
            className="w-full py-3.5 rounded-full border border-white/[0.1] text-muted-foreground hover:bg-white/[0.04] font-medium text-lg text-center transition-all"
          >
            下载曲谱
          </a>
        )}
        <button
          onClick={() => {
            if (navigator.share) {
              navigator.share({ title: "我用AI定制了一首歌", text: "用SongCraft为你的ta写一首歌吧" });
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
