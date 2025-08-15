# Windows 11 to Windows 10 ISO Patcher for Boot Camp

This tool modifies Windows 11 ISOs to bypass TPM and Secure Boot requirements while **spoofing as Windows 10** for Boot Camp compatibility on Intel-based Macs.

## 🎯 What This Tool Does

1. **Extracts version information** from a Windows 10 ISO (build numbers, product IDs, registry data)
2. **Applies Windows 10 metadata** to a Windows 11 ISO (volume labels, WIM metadata, registry entries)
3. **Bypasses TPM 2.0 and Secure Boot** requirements for Intel Mac compatibility
4. **Creates a hybrid ISO** that Boot Camp recognizes as Windows 10 but installs Windows 11

## 🖥️ System Requirements

- **macOS** (tested on macOS 10.15+)
- **Intel-based Mac** with Boot Camp support
- **At least 15GB free disk space** for temporary files during processing
- **Homebrew** package manager
- **Two ISO files**: Windows 11 (source) and Windows 10 22H2 (for metadata extraction)

## 📦 Required Dependencies

### System Tools
- **wimlib**: For handling Windows Imaging Format (WIM) files
- **hivex**: For offline Windows registry editing
- **mkisofs**: For ISO creation (from cdrtools package, with pycdlib fallback)
- **pkg-config**: Required for building some dependencies

### Python Libraries
- **pycdlib**: Python library for ISO manipulation and creation
- **argparse**: Command line argument parsing (usually built-in)

## 🚀 Quick Installation

1. **Clone or download** this repository
2. **Run the installation script**:
   ```bash
   ./install_dependencies.sh
   ```
3. **Follow the prompts** - the script will install all required dependencies via Homebrew

### Manual Installation

If you prefer to install dependencies manually:

```bash
# Install system dependencies
brew install wimlib hivex cdrtools pkg-config

# Install Python dependencies  
pip3 install pycdlib
```

## 📋 Usage

### 🚀 Quick Launch (Recommended)

Use the included launch script for automatic dependency checking and GUI startup:

```bash
./launch.sh
```

The launch script will:
- ✅ Check all dependencies and provide install instructions for missing ones
- ✅ Launch the GUI application automatically
- ✅ Display helpful status messages and warnings

### 🖥️ GUI Usage

1. **Launch the application** using `./launch.sh` or `python3 main.py`
2. **Select your Windows 11 ISO** (source file to be patched)
3. **Select your Windows 10 ISO** (for Boot Camp spoofing metadata)
4. **Choose output location** for the patched ISO
5. **Click "Start Patching"** and wait for completion

### 💻 Manual Command Line Usage

You can also run the application directly:

```bash
python3 main.py
```

This will open the GUI interface where you can select your ISO files and output location.

## 🔧 How It Works

### Step 1: Windows 10 Metadata Extraction
- Extracts `boot.wim` and `install.wim` from Windows 10 ISO
- Captures version strings, build numbers, and product information
- Extracts registry data from Windows 10 SYSTEM hive
- Stores volume labels and ISO identifiers

### Step 2: Windows 11 ISO Processing  
- Extracts all files from Windows 11 ISO
- Locates `boot.wim` and `install.wim` files
- Prepares temporary directory structure

### Step 3: Boot.wim Modification
- Extracts Windows 11 `boot.wim` contents
- Modifies SYSTEM registry to add TPM/Secure Boot bypass keys:
  - `BypassTPMCheck = 1`
  - `BypassSecureBootCheck = 1`
  - `BypassRAMCheck = 1`
  - `BypassStorageCheck = 1`
  - `BypassCPUCheck = 1`
- Applies Windows 10 registry metadata for spoofing
- Rebuilds `boot.wim` with modifications

### Step 4: Install.wim Spoofing
- Updates all Windows 11 images in `install.wim`
- Replaces display names with Windows 10 equivalents
- Changes version descriptions to match Windows 10
- Maintains Windows 11 functionality while appearing as Windows 10

### Step 5: ISO Creation
- Uses Windows 10 volume labels (e.g., `CCSA_X64FRE_EN-US_DV5`)
- Creates bootable ISO with multiple fallback methods:
  1. **mkisofs** (preferred, supports files >4GB with ISO level 3)
  2. **genisoimage** (backup method)
  3. **pycdlib** (Python fallback)
- Validates output size against source to ensure completeness

## 🏃‍♂️ Running the Patcher

1. **Obtain your ISOs**:
   - Download Windows 11 22H2 ISO from Microsoft
   - Download Windows 10 22H2 ISO from Microsoft (for metadata)

2. **Run the patcher**:
   ```bash
   python3 main.py path/to/windows11.iso path/to/windows10.iso
   ```

3. **Monitor progress** - the tool provides detailed logging of each step

4. **Use with Boot Camp** - the output ISO can be used directly with Boot Camp Assistant

## 🔍 Verification

After completion, verify your patched ISO:

- **Size check**: Output should be similar to input Windows 11 ISO size (~5-6GB)
- **Boot Camp test**: Boot Camp Assistant should recognize it as Windows 10
- **File integrity**: All Windows 11 files should be present in the ISO

## 🛠️ Troubleshooting

### Common Issues

#### "boot.wim not found"
- Ensure your Windows 11 ISO is valid and not corrupted
- Some ISOs have different directory structures - check the logs for extraction details

#### "wimlib was compiled with --without-fuse"
- This should not occur with the current version (we use extract/update instead of mounting)
- If it does occur, reinstall wimlib: `brew reinstall wimlib`

#### "mkisofs: File too large for current mkisofs settings"  
- This should not occur (we use ISO level 3 which supports large files)
- If it does, the tool will automatically fall back to pycdlib

#### Output ISO much smaller than input
- Indicates extraction or creation failure
- Check the detailed logs for specific error messages
- Ensure sufficient disk space (15GB+ recommended)

#### Boot Camp still rejects the ISO
- Verify the Windows 10 ISO you used for metadata extraction is genuine
- Try using a different Windows 10 22H2 ISO for metadata
- Check that your Intel Mac supports the version of Boot Camp you're using

### Debug Mode

For detailed debugging information:

```bash
# The tool provides extensive logging by default
# Check the console output for step-by-step progress
python3 main.py win11.iso win10.iso 2>&1 | tee patcher.log
```

### Dependency Issues

```bash
# Verify all dependencies
./install_dependencies.sh --verify

# Test all tools
./install_dependencies.sh --test

# Reinstall dependencies
brew reinstall wimlib hivex cdrtools
pip3 install --upgrade pycdlib
```

## 🔒 Security Considerations

- This tool modifies Windows installation files to bypass hardware security requirements
- The resulting Windows installation will have **reduced security** due to disabled TPM and Secure Boot
- Only use this on systems where you understand and accept these security implications
- The tool only modifies local files and does not connect to the internet

## ⚖️ Legal Notice

- This tool is for educational and compatibility purposes only
- Users must own valid licenses for both Windows 11 and Windows 10
- Microsoft's terms of service and licensing agreements still apply
- This tool does not provide or include any Microsoft software

## 🔧 Advanced Configuration

### Custom Registry Modifications

The tool creates standard TPM bypass entries. For custom modifications, edit the `modify_system_registry` function in `main.py`.

### ISO Creation Options

The tool tries multiple ISO creation methods automatically. To force a specific method, modify the `create_iso` function.

### Windows 10 Metadata Sources

By default, the tool extracts comprehensive metadata from the Windows 10 ISO. The key extracted information includes:

- **Boot.wim metadata**: Version strings, build numbers
- **Install.wim metadata**: Edition names, descriptions  
- **Registry data**: Product type, computer name settings
- **Product information**: ei.cfg, licensing data
- **Volume labels**: ISO filesystem identifiers

## 📚 Technical Details

### File Structure
```
WinMac11/
├── main.py                 # Main patcher application
├── install_dependencies.sh # Dependency installation script
├── README.md              # This documentation
└── (generated files)
    ├── temp directories/   # Temporary extraction/build folders
    └── output.iso         # Final patched ISO
```

### Supported Windows Versions

**Windows 11 (Source):**
- Windows 11 22H2 (recommended)
- Windows 11 21H2
- Most Windows 11 editions (Home, Pro, Enterprise)

**Windows 10 (Metadata):**
- Windows 10 22H2 (recommended for best compatibility)
- Windows 10 21H2
- Windows 10 20H2

### Boot Camp Compatibility

This tool has been tested with:
- Boot Camp Assistant 6.1+ on macOS 10.15+
- Intel MacBook Pro (2015-2020)
- Intel MacBook Air (2015-2020) 
- Intel iMac (2015-2020)
- Intel Mac mini (2014-2020)

## 🤝 Contributing

This project welcomes contributions! Areas for improvement:

- Support for additional Windows versions
- Enhanced metadata extraction
- Better error handling and recovery
- GUI interface
- Automated testing

## 📋 Changelog

### Version 2.0 (Windows 10 Spoofing Update)
- ✅ Added Windows 10 metadata extraction and spoofing
- ✅ Enhanced Boot Camp compatibility
- ✅ Improved ISO creation with multiple fallback methods
- ✅ Added comprehensive logging and debugging
- ✅ Fixed file size limitations (ISO level 3 support)
- ✅ Removed macFUSE dependency

### Version 1.0 (Original TPM Bypass)
- ✅ Basic TPM and Secure Boot bypass
- ✅ Windows 11 boot.wim modification
- ✅ ISO extraction and creation

## 🆘 Support

If you encounter issues:

1. **Check this README** for troubleshooting steps
2. **Run the dependency checker**: `./install_dependencies.sh --verify`
3. **Review the console output** for specific error messages
4. **Ensure you have valid Windows ISOs** from Microsoft
5. **Verify sufficient disk space** (15GB+ recommended)

## 📄 License

This project is provided "as-is" without warranty. Users are responsible for complying with all applicable laws and licensing agreements.

---

**Made for Intel Mac users who want to run Windows 11 via Boot Camp** 🍎➡️🪟 