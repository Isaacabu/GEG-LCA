import { AssetImage } from "./AssetImage.js";

export function BrandLogo() {
  return (
    <AssetImage
      src="/assets/logo.png"
      alt="GEG AAA"
      style={{ width: 36, height: 36, borderRadius: 8, objectFit: "contain" }}
      fallback={<div className="brand-mark" />}
    />
  );
}
