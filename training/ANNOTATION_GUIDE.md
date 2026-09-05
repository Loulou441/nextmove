# Annotation Guide for Sports Detection

Complete guide for annotating pickleball and soccer videos for model training.

## Overview

Quality annotations are critical for model performance. This guide provides detailed instructions for consistent, accurate annotations.

## General Principles

### 1. Completeness
- Annotate ALL visible objects in every frame
- Include partially visible objects (>20% visible)
- Don't skip difficult cases - they help the model learn

### 2. Consistency
- Use the same class labels throughout
- Apply the same bounding box tightness
- Follow the same rules for edge cases

### 3. Accuracy
- Tight bounding boxes with minimal padding
- Correct class labels
- Proper handling of occlusions

## Pickleball Annotation

### Class Definitions

#### 1. Ball (class 0)
- **What**: The pickleball itself
- **Bounding box**: Tight around the ball
- **Notes**: 
  - Annotate even when blurry (motion blur)
  - Include when partially occluded by net/player
  - Skip if completely invisible

#### 2. Player (class 1)
- **What**: Any person on the court
- **Bounding box**: Full body from head to feet
- **Notes**:
  - Include players in background
  - Include referee if on court
  - Exclude spectators off court

#### 3. Paddle (class 2)
- **What**: Pickleball paddle held by player
- **Bounding box**: Just the paddle, not the hand
- **Notes**:
  - Only annotate when clearly visible
  - Skip if completely occluded by player body
  - Include paddle head and handle

#### 4. Court Line (class 3)
- **What**: Court boundaries, kitchen line, centerline
- **Bounding box**: Segment of visible line
- **Notes**:
  - Annotate major lines only (not all grid lines)
  - One box per continuous line segment
  - Include baseline, sidelines, kitchen line

#### 5. Net (class 4)
- **What**: The net itself (mesh)
- **Bounding box**: Visible portion of net
- **Notes**:
  - One box for entire visible net
  - Include top tape/band
  - Exclude net posts (separate class)

#### 6. Net Post (class 5)
- **What**: Vertical posts supporting the net
- **Bounding box**: From ground to top of post
- **Notes**:
  - Annotate each post separately
  - Include any visible support structure

### Pickleball Examples

```
Good annotation:
- Ball: tight box, even if small (5-10 pixels)
- Player: full body, feet to head
- Paddle: just paddle, not arm
- Lines: continuous segments

Bad annotation:
- Ball: too much padding around ball
- Player: cropped at waist or missing feet
- Paddle: includes entire arm
- Lines: tiny disconnected segments
```

## Soccer Annotation

### Class Definitions

#### 1. Ball (class 0)
- **What**: The soccer ball
- **Bounding box**: Tight around the ball
- **Notes**:
  - Annotate even when small/distant
  - Include when partially occluded
  - Skip if completely invisible

#### 2. Player (class 1)
- **What**: Any player on the field
- **Bounding box**: Full body from head to feet
- **Notes**:
  - Include all players (both teams)
  - Include goalkeeper
  - Include referee if on field
  - Exclude bench players and spectators

#### 3. Goal (class 2)
- **What**: Goal posts and net structure
- **Bounding box**: Entire visible goal structure
- **Notes**:
  - One box per goal
  - Include posts, crossbar, and net
  - Annotate even if partially visible

#### 4. Field Line (class 3)
- **What**: Field boundaries, penalty box, center circle
- **Bounding box**: Segment of visible line
- **Notes**:
  - Annotate major lines (boundaries, penalty box)
  - One box per continuous line segment
  - Skip minor markings

### Soccer Examples

```
Good annotation:
- Ball: tight box, even when distant
- Player: all players, full body
- Goal: entire structure as one box
- Lines: major field markings

Bad annotation:
- Ball: missing when small
- Player: only nearby players annotated
- Goal: separate boxes for each post
- Lines: every tiny line segment
```

## Bounding Box Guidelines

### Tightness
- **Correct**: 1-2 pixel padding around object
- **Too loose**: Large empty space around object
- **Too tight**: Cutting off parts of object

### Aspect Ratio
- Maintain natural object proportions
- Don't force square boxes on rectangular objects
- Ball should be roughly square

### Occlusion Handling
- **Partial occlusion** (>50% visible): Annotate visible portion
- **Heavy occlusion** (<50% visible): Skip or annotate if position clear
- **Complete occlusion**: Skip

## Quality Checklist

Before submitting annotations:

- [ ] All visible objects annotated
- [ ] Bounding boxes are tight (1-2 pixel padding)
- [ ] Correct class labels used
- [ ] No duplicate boxes for same object
- [ ] Partially occluded objects included
- [ ] Consistent annotation style throughout
- [ ] Edge cases handled appropriately

## Common Mistakes

### 1. Inconsistent Tightness
❌ Some boxes tight, others loose
✅ All boxes consistently tight

### 2. Missing Small Objects
❌ Skipping distant balls or players
✅ Annotating all visible objects regardless of size

### 3. Wrong Class Labels
❌ Labeling paddle as player
✅ Using correct class for each object

### 4. Duplicate Annotations
❌ Multiple boxes for same object
✅ One box per object

### 5. Including Background
❌ Annotating spectators, benches, etc.
✅ Only objects on playing surface

## Annotation Workflow

### Recommended Process

1. **First pass**: Annotate obvious objects (players, ball)
2. **Second pass**: Add equipment (paddles, goals)
3. **Third pass**: Add court/field elements (lines, net)
4. **Review pass**: Check for missed objects and errors

### Frame Selection

For training efficiency:
- Extract frames at 5 fps from videos
- Focus on action sequences (rallies, plays)
- Include variety of conditions:
  - Different lighting (indoor/outdoor, day/night)
  - Different angles (court-side, elevated)
  - Different distances (close-up, wide shot)
  - Different player positions

### Minimum Dataset Size

- **Minimum viable**: 100 images per class
- **Good performance**: 500 images per class
- **Excellent performance**: 1000+ images per class

## Tool-Specific Tips

### CVAT
- Use keyboard shortcuts (N for new box, F for finish)
- Use interpolation for tracking objects across frames
- Export in YOLO format

### Label Studio
- Create project with YOLO template
- Use rectangle tool for bounding boxes
- Export as YOLO

### Roboflow
- Upload images in batches
- Use smart polygon for complex shapes
- Auto-export to YOLO format

## Validation

After annotation, validate using:

```bash
python scripts/validate_annotations.py \
  --images data/frames/ \
  --labels data/annotations/ \
  --classes 6
```

Fix any errors reported before training.

## Tips for Speed

1. **Keyboard shortcuts**: Learn tool shortcuts
2. **Batch similar frames**: Annotate similar scenes together
3. **Use interpolation**: For tracking across frames
4. **Start simple**: Annotate main objects first
5. **Take breaks**: Maintain quality over speed

## Questions?

Common questions:

**Q: Should I annotate blurry objects?**
A: Yes, if you can identify what it is

**Q: What about objects at frame edge?**
A: Annotate if >20% visible

**Q: How tight should boxes be?**
A: 1-2 pixel padding maximum

**Q: Should I annotate shadows?**
A: No, only actual objects

**Q: What about reflections?**
A: No, only real objects

## Next Steps

1. Set up annotation tool
2. Annotate 10 test images
3. Review with team for consistency
4. Annotate full dataset
5. Validate annotations
6. Begin training
