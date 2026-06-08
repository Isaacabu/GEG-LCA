import { AssetImage } from "./AssetImage.js";
import { InteractiveBuildingHero } from "./InteractiveBuildingHero.js";

export function HeroBuildingVisual({
  onHotspot,
}: {
  onHotspot?: (id: "roof" | "wall" | "window" | "door" | "floor") => void;
}) {
  return (
    <div className="hero-img-wrap">
      <AssetImage
        src="/assets/hero-building.png"
        alt="Gebaeudevisual"
        fallback={<InteractiveBuildingHero onHotspot={onHotspot} />}
      />
    </div>
  );
}
