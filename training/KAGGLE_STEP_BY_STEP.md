# Pickleball Model — Full Kaggle Guide (Setup → Train → Ship)

Everything you need to fine-tune the pickleball detector on Kaggle's free GPU
and get it into the iOS app. The notebook is `kaggle_train_pickleball.ipynb`.

---

## PART A — Before Kaggle (5 minutes)

### A1. Get a free Roboflow API key (for the dataset)
1. Sign up at https://app.roboflow.com (free).
2. Go to https://app.roboflow.com/settings/api
3. Copy your **Private API Key**. You'll paste it into the notebook (cell 2).

### A2. Get a Kaggle account + phone-verify (needed for GPU)
1. Sign up at https://www.kaggle.com
2. Go to Settings → **Phone Verification** and verify. This unlocks free GPU
   (~30 hrs/week). Without it, GPU is disabled.

---

## PART B — Set up the notebook on Kaggle (5 minutes)

### B1. Create the notebook
1. Kaggle → **Create → New Notebook**.
2. **File → Import Notebook → Upload** and choose:
   `training/kaggle_train_pickleball.ipynb`

### B2. Turn on the GPU (critical)
1. Right sidebar → **Settings** (or the ⋮ menu) → **Accelerator**.
2. Select **GPU T4 x2**.
3. Also make sure **Internet** is **On** (Settings → Internet) — the notebook
   downloads the dataset and pip packages.

### B3. Paste your Roboflow key
In cell 2, set:
```python
ROBOFLOW_API_KEY = 'paste_your_key_here'
```

---

## PART C — Run the training (~2–4 hours, mostly hands-off)

Click **Run All** (or run cells top to bottom). What each step does:

1. **Install** — installs ultralytics, roboflow, coremltools. Prints
   `CUDA available: True` if the GPU is on (if False, fix B2).
2. **Download dataset** — pulls the public pickleball dataset in YOLO format.
3. **Train** — loads COCO-pretrained `yolo11n.pt` (transfer learning) and
   fine-tunes for 100 epochs on pickleball. This is the long step.
4. **Validate** — prints the REAL metrics (mAP@0.5, precision, recall). Write
   these down — they're your honest performance numbers.
5. **Export** — converts the best weights to Core ML.
6. **Download artifacts** — see Part D.

> Tip: Kaggle notebooks stop if the tab is closed for too long. Either keep the
> tab open, or use **Save Version → Save & Run All (Commit)** to run it in the
> background and collect outputs when done.

### If you hit a wall
- `CUDA available: False` → Accelerator isn't set to GPU (redo B2).
- Roboflow error → key missing/wrong, or Internet is Off.
- Out of memory → in the train cell, lower `batch=16` to `batch=8`.

---

## PART D — Get the files off Kaggle

After the run, open the right panel → **Output** (or **Data → Output**). Download:

1. **The Core ML model** — the exported `.mlpackage` (look under
   `runs/train/pickleball_detector/weights/` or the export output folder). This
   is the file the app needs.
2. **`best.pt`** — `runs/train/pickleball_detector/weights/best.pt`
   (PyTorch weights; keep as your source of truth / for re-export).
3. **Training charts** — the `runs/train/pickleball_detector/` folder has
   `results.png`, `confusion_matrix.png`, etc. Great for a report/demo slide.

If Kaggle exported a folder rather than a single file, zip it and download the zip.

---

## PART E — Put the model into the iOS app

1. Rename the exported Core ML package to exactly:
   ```
   PickleballDetector_v1.mlpackage
   ```
2. Copy it into the app at:
   ```
   nextmove/Models/Pickleball/PickleballDetector_v1.mlpackage
   ```
   (Replace the existing placeholder there.)
3. In **Xcode**:
   - Drag the `.mlpackage` into the `Models/Pickleball` group **if it's not
     already referenced**.
   - Select the file → in the right panel, check **Target Membership → nextmove**.
   - Confirm it's in **Build Phases → Copy Bundle Resources**.
4. **Product → Clean Build Folder** (⌘⇧K), then build & run.

`ModelManager` already looks for `PickleballDetector_v1` in `Models/Pickleball`
(both `.mlpackage` and `.mlmodelc`), so no code change is needed.

---

## PART F — Switch the app from demo mode to the real model

Right now the app runs mock analysis. In
`nextmove/ViewModels/RecordingViewModel.swift`, `processRecording` calls
`runDemoAnalysis`. To use the real pipeline:

1. Swap the demo call for the real pipeline (`AnalysisPipeline.withStandardCoaching`
   / `withLLMCoaching`), which routes through `ObjectDetector` → your new model.
2. Test on a real pickleball clip.

> Keep the demo path around behind a flag — it's a reliable fallback for demos
> if the model misses on unusual footage.

Tell me when your model is downloaded and I'll wire the app to use it for real
(and keep demo mode as a safety net).

---

## Honest reporting reminder

- The mAP/precision/recall from Part C step 4 are your **real** numbers — quote
  those, not invented ones.
- Accurate one-liner: "Transfer learning from a COCO-pretrained YOLO11 backbone,
  fine-tuned on a public pickleball dataset, exported to Core ML for on-device
  inference." All true, all solid.
