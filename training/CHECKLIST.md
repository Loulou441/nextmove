# Training Pipeline Checklist

Use this checklist to track your progress through the training pipeline.

## Phase 1: Setup ✅

- [x] Python training pipeline created
- [x] All scripts implemented
- [x] Documentation complete
- [ ] Run `bash scripts/quick_start.sh`
- [ ] Run `python scripts/test_pipeline.py`
- [ ] Verify all checks pass

**Time:** 5 minutes  
**Status:** Ready to execute

---

## Phase 2: Data Collection

- [ ] Collect 5-10 pickleball videos
- [ ] Place videos in `data/raw/`
- [ ] Videos are 1-5 minutes each
- [ ] Videos have clear visibility
- [ ] Videos include variety (angles, lighting)

**Time:** Varies  
**Goal:** 10-30 minutes of footage

---

## Phase 3: Frame Extraction

- [ ] Run `python scripts/extract_frames.py data/raw/ data/frames/ --fps 5`
- [ ] Verify frames extracted: `ls data/frames/ | wc -l`
- [ ] Expected: 300-900 frames
- [ ] Frames are clear and usable

**Time:** 5-10 minutes  
**Goal:** 300+ frames

---

## Phase 4: Annotation (Most Time-Consuming)

### Setup Annotation Tool
- [ ] Choose tool (CVAT, Roboflow, Label Studio)
- [ ] Create account/install tool
- [ ] Create project: "Pickleball Detection"
- [ ] Add classes: ball, player, paddle, court_line, net, net_post

### Annotate Frames
- [ ] Upload frames to annotation tool
- [ ] Read `ANNOTATION_GUIDE.md`
- [ ] Annotate first 10 frames (practice)
- [ ] Review quality with team
- [ ] Annotate remaining frames
- [ ] Export in YOLO format
- [ ] Extract to `data/annotations/`

### Quality Check
- [ ] All frames annotated
- [ ] Bounding boxes are tight
- [ ] Correct class labels used
- [ ] No duplicate boxes
- [ ] Consistent annotation style

**Time:** 4-8 hours (for 300 frames)  
**Goal:** 100% annotation coverage

---

## Phase 5: Validation

- [ ] Run `python scripts/validate_annotations.py --images data/frames/ --labels data/annotations/ --classes 6`
- [ ] Review validation report
- [ ] Fix any errors reported
- [ ] Re-run validation
- [ ] All checks pass

**Time:** 5-10 minutes  
**Goal:** Zero errors

---

## Phase 6: Dataset Split

- [ ] Run `python scripts/split_dataset.py --images data/frames/ --labels data/annotations/ --output data/`
- [ ] Verify split: `ls data/train/images/ | wc -l`
- [ ] Train set: ~70% of images
- [ ] Val set: ~20% of images
- [ ] Test set: ~10% of images

**Time:** 1 minute  
**Goal:** Proper train/val/test split

---

## Phase 7: Training

### Start Training
- [ ] Activate virtual environment: `source venv/bin/activate`
- [ ] Run `python scripts/train_yolo.py --config configs/pickleball_yolo.yaml`
- [ ] Monitor progress: `tail -f runs/train/pickleball_detector/results.txt`

### Monitor Training
- [ ] Training started successfully
- [ ] mAP improving over epochs
- [ ] No out-of-memory errors
- [ ] Training completes or early stops

### Review Results
- [ ] Check final mAP@0.5 (target: > 0.85)
- [ ] Check inference time (target: < 200ms)
- [ ] Review per-class metrics
- [ ] Best model saved: `runs/train/pickleball_detector/weights/best.pt`

**Time:** 2-4 hours (GPU) or 24-48 hours (CPU)  
**Goal:** mAP@0.5 > 0.85

---

## Phase 8: Validation

- [ ] Run `python scripts/validate.py --model runs/train/pickleball_detector/weights/best.pt --config configs/pickleball_yolo.yaml`
- [ ] Review validation metrics
- [ ] mAP@0.5 > 0.85 ✓
- [ ] Inference < 200ms ✓
- [ ] Per-class performance acceptable
- [ ] Save validation report

**Time:** 5 minutes  
**Goal:** Meet performance targets

---

## Phase 9: Core ML Conversion

- [ ] Run `python scripts/convert_to_coreml.py --model runs/train/pickleball_detector/weights/best.pt --config configs/pickleball_yolo.yaml --output models/exported/`
- [ ] Conversion successful
- [ ] Model size < 10MB
- [ ] Validation passes
- [ ] Model file: `models/exported/PickleballDetector_v1.mlmodel`

**Time:** 5 minutes  
**Goal:** Core ML model ready

---

## Phase 10: iOS Deployment

- [ ] Copy model: `cp models/exported/PickleballDetector_v1.mlmodel ../Models/Pickleball/`
- [ ] Open Xcode: `open ../nextmove.xcodeproj`
- [ ] Verify model in Project Navigator
- [ ] Check "Copy Bundle Resources" build phase
- [ ] Build project successfully
- [ ] No build errors

**Time:** 5 minutes  
**Goal:** Model integrated in iOS app

---

## Phase 11: Testing

### In-App Testing
- [ ] Launch app on device/simulator
- [ ] Record or import test video
- [ ] Start analysis
- [ ] Frame extraction works
- [ ] Objects detected correctly
- [ ] Tracking is stable
- [ ] Coaching feedback generated

### Quality Check
- [ ] Detection confidence: 0.7-0.9
- [ ] Track IDs stable across frames
- [ ] Analysis time < 2 min for 5-min video
- [ ] Coaching insights: 3-5 actionable items
- [ ] No crashes or errors

**Time:** 10-15 minutes  
**Goal:** End-to-end pipeline working

---

## Phase 12: Iteration (Optional)

### Identify Issues
- [ ] Test with multiple videos
- [ ] Document failure cases
- [ ] Identify weak classes
- [ ] Note edge cases

### Improve Model
- [ ] Collect more data for weak areas
- [ ] Annotate new frames
- [ ] Re-split dataset
- [ ] Retrain with more data
- [ ] Convert to v2
- [ ] Deploy and test

**Time:** Varies  
**Goal:** Continuous improvement

---

## Success Criteria

### Minimum Viable Model
- [x] Training pipeline complete
- [ ] 100+ annotated images
- [ ] mAP@0.5 > 0.7
- [ ] Model runs on iOS
- [ ] Basic detection works

### Production Ready Model
- [x] Training pipeline complete
- [ ] 500+ annotated images
- [ ] mAP@0.5 > 0.85
- [ ] Inference < 200ms
- [ ] Model size < 10MB
- [ ] Stable tracking
- [ ] Quality coaching feedback

---

## Troubleshooting

### If Training Fails
- [ ] Check GPU availability
- [ ] Reduce batch size
- [ ] Verify dataset split
- [ ] Check annotation quality
- [ ] Review error logs

### If Accuracy is Low
- [ ] Collect more data
- [ ] Improve annotations
- [ ] Train longer
- [ ] Check class balance
- [ ] Review failure cases

### If Conversion Fails
- [ ] Check coremltools version
- [ ] Try without quantization
- [ ] Verify model trained successfully
- [ ] Check Python environment

---

## Resources

- [ ] Read `README.md` for full documentation
- [ ] Review `ANNOTATION_GUIDE.md` for annotation help
- [ ] Follow `WORKFLOW_EXAMPLE.md` for step-by-step guide
- [ ] Use `QUICK_REFERENCE.md` for command reference
- [ ] Check `POC_STATUS.md` for project status

---

## Timeline Estimate

| Phase | Time | Status |
|-------|------|--------|
| Setup | 5 min | ✅ Ready |
| Data Collection | Varies | ⏳ Pending |
| Frame Extraction | 10 min | ⏳ Pending |
| Annotation | 4-8 hours | ⏳ Pending |
| Validation | 10 min | ⏳ Pending |
| Dataset Split | 1 min | ⏳ Pending |
| Training | 2-4 hours | ⏳ Pending |
| Validation | 5 min | ⏳ Pending |
| Conversion | 5 min | ⏳ Pending |
| Deployment | 5 min | ⏳ Pending |
| Testing | 15 min | ⏳ Pending |

**Total:** 6-12 hours (mostly annotation + GPU time)

---

## Next Action

**Your next step:** Run `bash scripts/quick_start.sh` to set up the environment.

After setup, start collecting and annotating data!
