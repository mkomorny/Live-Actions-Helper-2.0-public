// The host <-> webview contract for BBenCut, mirroring
// tools\breakdowns\src\protocol.ts. PURE / SDK-free so it can be imported by
// both the webview (main.ts) and, later, the host context-builder.
import type { RollGroup, SliceDefinition } from "./slicer.js";

/** The 10 cut procedures BBenCut's own UI shipped -- see NOTICE.txt and the
 *  "Scope decision" in the approved plan for why only these 10. */
export type AlgorithmId =
  | "BBCutProc11"
  | "ChooseCutProc"
  | "ChooseBlockProc"
  | "WarpCutProc1"
  | "SQPusher1"
  | "SQPusher2"
  | "CageCut"
  | "TimelineCut"
  | "BBCPPermute"
  | "ThrashCutProc1";

/** Host -> webview: everything the dialog needs to render and seed its
 *  controls. No Arrangement-clip read support exists yet (that's Step 4 of
 *  the plan), so totalLengthBeats/loopLengthBeats are honest static
 *  defaults, not values read off "the selected clip". */
export interface BBenCutContext {
  hasClip: boolean;
  clipName?: string;
  filePath?: string;
  totalLengthBeats: number;
  loopLengthBeats: number;
  tempo?: number;
}

/** Webview -> host, on Apply. Cancel/Escape posts null instead. Apply posts
 *  pure JSON, nothing else -- the dialog does no LOM/OSC work itself. */
export interface BBenCutRequest {
  algorithm: AlgorithmId;
  params: Record<string, number>;
  totalLengthBeats: number;
  loopLengthBeats: number;
  slices: SliceDefinition[];
  rollGroups: RollGroup[];
}
