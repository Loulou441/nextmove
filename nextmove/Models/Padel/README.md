# Padel Detector (app bundle)

`ModelManager` looks up `SportType.padel` at bundle path:

```
Models/Padel/PadelDetector_v1.mlpackage
```

Drop the trained model here and add it to the Xcode target's
"Copy Bundle Resources" so it ships with the app.

The model is trained on the **Plaimaker "padel-tkrqs"** dataset (Roboflow
Universe). See `training/PADEL_STEP_BY_STEP.md` and the repo-root
`Models/Padel/README.md` for the full download → train → export pipeline.

Until this model is present, padel analysis uses the app's demo/mock path.
