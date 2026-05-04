import { useState } from "react";
import { Tier, Audience, Occasion, Style } from "@/types";
import { HomeSection } from "@/sections/HomeSection";
import { CreateSection } from "@/sections/CreateSection";
import { ResultSection } from "@/sections/ResultSection";

type Page = "home" | "create" | "result";

export interface SongDraft {
  tier: Tier;
  audience: Audience | "";
  occasion: Occasion | "";
  personalNote: string;
  style: Style | "";
}

export interface OrderInfo {
  orderId: string;
  price: number;
  tier: Tier;
}

function App() {
  const [page, setPage] = useState<Page>("home");
  const [draft, setDraft] = useState<SongDraft>({
    tier: "premium",
    audience: "",
    occasion: "",
    personalNote: "",
    style: "",
  });
  const [order, setOrder] = useState<OrderInfo | null>(null);

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#1a1a2e] via-[#16213e] to-[#0f3460] text-white">
      <div className="mx-auto max-w-md min-h-screen p-4 flex flex-col">
        {page === "home" && (
          <HomeSection
            draft={draft}
            onDraftChange={setDraft}
            onStart={() => setPage("create")}
          />
        )}
        {page === "create" && (
          <CreateSection
            draft={draft}
            onDraftChange={setDraft}
            onBack={() => setPage("home")}
            onOrderCreated={(order) => {
              setOrder(order);
              setPage("result");
            }}
          />
        )}
        {page === "result" && order && (
          <ResultSection
            order={order}
            onNewSong={() => {
              setDraft({ tier: "premium", audience: "", occasion: "", personalNote: "", style: "" });
              setOrder(null);
              setPage("home");
            }}
          />
        )}
      </div>
    </div>
  );
}

export default App;
