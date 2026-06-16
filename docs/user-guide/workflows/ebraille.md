# eBraille Workflow

**Creating and distributing digital braille files.**

---

## 📋 Workflow Steps

### 1. **Source Acquisition**
- **Purpose**: Obtain digital source
- **Tasks**:
  - Receive file from teacher/student
  - Verify file format (DOCX, PDF, TXT, etc.)
  - Check for DRM or restrictions
- **Supported Formats**:
  - Microsoft Word (.docx)
  - PDF (.pdf)
  - Plain text (.txt)
  - EPUB (.epub)
  - HTML (.html)

### 2. **Text Extraction**
- **Purpose**: Convert to editable text
- **Tasks**:
  - Extract text from PDFs
  - Clean up formatting
  - Remove images or convert to descriptions
- **Tools**: Pandoc, Adobe Acrobat

### 3. **Braille Translation**
- **Purpose**: Convert text to braille
- **Tasks**:
  - Select braille code
  - Configure translation settings
  - Run translation
- **Tools**: LibLouis

### 4. **Formatting**
- **Purpose**: Structure braille output
- **Tasks**:
  - Add page numbers
  - Configure headers/footers
  - Set up volume structure (for multi-volume)
  - Add navigation markers
- **Output**: .brf (Braille Ready Format)

### 5. **Validation**
- **Purpose**: Ensure quality
- **Tasks**:
  - Check for translation errors
  - Verify formatting
  - Test with braille display
- **Tools**: BRLTTY, braille display

### 6. **Distribution**
- **Purpose**: Deliver to student
- **Tasks**:
  - Select delivery method
  - Package files
  - Send via email/portal
- **Delivery Methods**:
  - Email attachment
  - Learning management system
  - USB drive
  - Cloud storage link

---
## 💾 File Formats
   Format | Extension | Description | Use Case |
 |--------|-----------|-------------|----------|
 | **BRF** | .brf | Braille Ready Format | Standard digital braille |
 | **BRF (Grade 2)** | .brf | Contracted braille | Most common |
 | **BRF (Computer)** | .brf | 8-dot braille | Computing |
 | **PEF** | .pef | Portable Embosser Format | Embosser-ready |
 | **DTB** | .dtb | DAISY Digital Talking Book | Audio + braille |
 | **EPUB** | .epub | EPUB with braille | Accessible e-books |

---
## 🔌 Device Compatibility

### Braille Displays
 | Device | BRF Support | Notes |
 |--------|-------------|-------|
 | **Focus (Freedom Scientific)** | ✅ Yes | All models |
 | **JAWS Braille Display** | ✅ Yes | All models |
 | **BrailleNote (HumanWare)** | ✅ Yes | Requires conversion |
 | **Orbit Reader (APH)** | ✅ Yes | Native support |
 | **Brailliant (APH)** | ✅ Yes | All models |
 | **Esys/Eurobraille** | ✅ Yes | Requires plugin |

### Reading Apps
 | App | Platform | BRF Support |
 |-----|----------|-------------|
 | **BrailleBack** | iOS | ✅ Yes |
 | **Braille Screen Input** | Android | ✅ Yes |
 | **BRLTTY** | Linux | ✅ Yes |
 | **NVDA** | Windows | ✅ Yes (with plugin) |
 | **JAWS** | Windows | ✅ Yes |
 | **VoiceOver** | macOS/iOS | ✅ Yes |

---
## 📊 Quality Checklist

Before distribution, verify:
- [ ] All text is properly translated
- [ ] No untranslated symbols
- [ ] Correct braille code used
- [ ] Proper page breaks
- [ ] Headers/footers present
- [ ] Volume structure correct (if multi-volume)
- [ ] File opens in target device/app
- [ ] No formatting errors
- [ ] All special characters handled

---
## 🔗 Related Workflows
- [Braille Workflow](braille.md) - For physical braille
- [EPUB/DAISY Workflow](epub-daisy.md) - For accessible e-books
