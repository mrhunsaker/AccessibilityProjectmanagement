# 3-D Print Workflow

**Managing 3D printing for accessibility aids and tactile models.**

---

## Workflow Overview

```mermaid
graph TD
    A[3D Model] --> B[Preparation]
    B --> C[Printing]
    C --> D[Post-Processing]
    D --> E[QA]
    E --> F[Delivery]
```

---

## Detailed Steps

### 1. Model Acquisition/Creation
- **Purpose**: Obtain or create 3D model
- **Sources**:
  - Pre-made models (Thingiverse, etc.)
  - Custom designs
  - Scanned objects
- **File Formats**: STL, OBJ, 3MF

### 2. Preparation
- **Purpose**: Prepare model for printing
- **Tasks**:
  - Scale to appropriate size
  - Orient for optimal printing
  - Add supports if needed
  - Slice for printer

### 3. Printing
- **Purpose**: Produce physical object
- **Tasks**:
  - Select printer
  - Load filament
  - Configure printer settings
  - Start print job

### 4. Post-Processing
- **Purpose**: Finish the printed object
- **Tasks**:
  - Remove supports
  - Sand rough edges
  - Clean up surfaces
  - Add any additional components

### 5. Quality Assurance
- **Purpose**: Verify print quality
- **Checks**:
  - Dimensional accuracy
  - Surface quality
  - Structural integrity
  - Fit with other components

### 6. Delivery
- **Purpose**: Send to recipient
- **Tasks**:
  - Package securely
  - Include care instructions
  - Update filament inventory

---

## Best Practices

### Design Guidelines
- Design for the specific printer's capabilities
- Use appropriate wall thickness for structural integrity
- Consider support material removal in design

### Printing Tips
- Calibrate printer before each job
- Monitor first layer adhesion
- Use appropriate print speed for detail level

---

## Related Workflows

- [Tactile Graphics Workflow](tactile-graphics.md) - For 2D tactile elements
- [Braille Workflow](braille.md) - For accompanying text
