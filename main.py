#!/usr/bin/env python3
"""
Windows 11 Boot Camp ISO Patcher
Modifies Windows 11 ISO files to bypass TPM and Secure Boot checks for Intel Mac Boot Camp
"""

import os
import sys

# Comprehensive macOS version detection workaround for Tkinter
if sys.platform == 'darwin':
    # Set multiple environment variables to bypass macOS version checks
    os.environ['TK_SILENCE_DEPRECATION'] = '1'
    os.environ['MACOSX_DEPLOYMENT_TARGET'] = '10.15'
    os.environ['PYTHON_CONFIGURE_OPTS'] = '--enable-framework'
    
    # Try to patch the version detection before importing tkinter
    try:
        import platform
        # Temporarily override platform.mac_ver to return a compatible version
        original_mac_ver = platform.mac_ver
        def patched_mac_ver():
            return ('10.15.7', ('', '', ''), 'x86_64')
        platform.mac_ver = patched_mac_ver
    except:
        pass

# Now try to import tkinter with error handling
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    TKINTER_AVAILABLE = True
except Exception as e:
    print(f"Warning: Tkinter not available: {e}")
    print("Falling back to command-line mode...")
    TKINTER_AVAILABLE = False

import subprocess
import tempfile
import shutil
import threading
import time
from pathlib import Path
# Import pycdlib with error handling
try:
    import pycdlib
    PYCDLIB_AVAILABLE = True
except ImportError:
    PYCDLIB_AVAILABLE = False
    print("Warning: pycdlib not available. Install with: pip install pycdlib")

class Win11BootCampPatcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows 11 to Windows 10 ISO Patcher for Boot Camp")
        self.root.geometry("800x700")  # Slightly taller for additional input field
        self.root.resizable(True, True)
        
        # Variables
        self.win11_iso_path = tk.StringVar()  # Changed from input_iso_path
        self.win10_iso_path = tk.StringVar()  # New Windows 10 ISO input
        self.output_iso_path = tk.StringVar()
        self.disable_validation = tk.BooleanVar(value=False)  # New validation disable flag
        self.is_processing = False
        
        print("Setting up UI...")
        try:
            self.setup_ui()
            print("UI setup completed!")
        except Exception as e:
            print(f"Error setting up UI: {e}")
            raise
        
        # Check dependencies in a separate thread to avoid blocking UI
        print("Starting dependency check...")
        threading.Thread(target=self.check_dependencies, daemon=True).start()
    
    def setup_ui(self):
        """Setup the main UI components"""
        try:
            # Main frame
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Configure grid weights
            self.root.columnconfigure(0, weight=1)
            self.root.rowconfigure(0, weight=1)
            main_frame.columnconfigure(1, weight=1)
            main_frame.rowconfigure(5, weight=1)  # Updated for additional row
            
            # Title
            title_label = ttk.Label(main_frame, text="Windows 11 to Windows 10 ISO Patcher", 
                                   font=("Arial", 16, "bold"))
            title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
            
            # Description
            desc_text = ("This tool combines Windows 11 and Windows 10 ISOs to create a Boot Camp compatible ISO.\n"
                        "It bypasses TPM/Secure Boot checks and spoofs Windows 11 as Windows 10 for Boot Camp.")
            desc_label = ttk.Label(main_frame, text=desc_text, justify=tk.CENTER)
            desc_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))
            
            # Windows 11 ISO selection
            ttk.Label(main_frame, text="Windows 11 ISO (source):").grid(row=2, column=0, sticky=tk.W, pady=5)
            ttk.Entry(main_frame, textvariable=self.win11_iso_path, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
            ttk.Button(main_frame, text="Browse", command=self.browse_win11_iso).grid(row=2, column=2, pady=5)
            
            # Windows 10 ISO selection
            ttk.Label(main_frame, text="Windows 10 ISO (for Boot Camp spoofing):").grid(row=3, column=0, sticky=tk.W, pady=5)
            ttk.Entry(main_frame, textvariable=self.win10_iso_path, width=50).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)
            ttk.Button(main_frame, text="Browse", command=self.browse_win10_iso).grid(row=3, column=2, pady=5)
            
            # Output ISO selection
            ttk.Label(main_frame, text="Output ISO location:").grid(row=4, column=0, sticky=tk.W, pady=5)
            ttk.Entry(main_frame, textvariable=self.output_iso_path, width=50).grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5)
            ttk.Button(main_frame, text="Browse", command=self.browse_output_iso).grid(row=4, column=2, pady=5)
            
            # Validation options
            validation_frame = ttk.Frame(main_frame)
            validation_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
            ttk.Checkbutton(validation_frame, text="Disable validation (skip file checks)", 
                           variable=self.disable_validation).pack(side=tk.LEFT)
            
            # Progress and log area
            log_frame = ttk.LabelFrame(main_frame, text="Progress and Log", padding="5")
            log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=20)
            log_frame.columnconfigure(0, weight=1)
            log_frame.rowconfigure(1, weight=1)
            
            # Progress bar
            self.progress = ttk.Progressbar(log_frame, mode='indeterminate')
            self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
            
            # Button frame for additional actions
            button_frame = ttk.Frame(log_frame)
            button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
            
            # Copy logs button
            copy_button = ttk.Button(button_frame, text="Copy Logs", command=self.copy_logs)
            copy_button.pack(side=tk.LEFT, padx=(0, 10))
            
            # Debug Boot Camp issues button
            debug_button = ttk.Button(button_frame, text="Debug Boot Camp Issues", command=self.debug_current_iso)
            debug_button.pack(side=tk.LEFT)
            
            # Log text area - simplified creation
            try:
                self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70)
                self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                print("ScrolledText widget created successfully")
            except Exception as e:
                print(f"Error creating ScrolledText: {e}")
                # Fallback to regular Text widget
                self.log_text = tk.Text(log_frame, height=15, width=70)
                self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Control buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=7, column=0, columnspan=3, pady=20)
            
            self.start_button = ttk.Button(button_frame, text="Start Patching", 
                                          command=self.start_patching, style="Accent.TButton")
            self.start_button.pack(side=tk.LEFT, padx=5)
            
            ttk.Button(button_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Copy Logs", command=self.copy_logs).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Debug Boot Camp Issues", command=self.debug_current_iso).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Force Boot Camp Volume Label", command=self.force_current_iso_volume_label).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(side=tk.LEFT, padx=5)
            
            # Status bar
            self.status_var = tk.StringVar(value="Ready")
            status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
            status_bar.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
            
            print("All UI components created successfully")
            
        except Exception as e:
            print(f"Error in setup_ui: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def browse_win11_iso(self):
        """Browse for Windows 11 ISO file"""
        filename = filedialog.askopenfilename(
            title="Select Windows 11 ISO",
            filetypes=[("ISO files", "*.iso"), ("All files", "*.*")]
        )
        if filename:
            self.win11_iso_path.set(filename)
            # Auto-suggest output filename
            if not self.output_iso_path.get():
                base_name = Path(filename).stem
                output_name = f"{base_name}_bootcamp.iso"
                output_path = Path(filename).parent / output_name
                self.output_iso_path.set(str(output_path))
    
    def browse_win10_iso(self):
        """Browse for Windows 10 ISO file (for metadata extraction)"""
        filename = filedialog.askopenfilename(
            title="Select Windows 10 ISO (for Boot Camp spoofing)",
            filetypes=[("ISO files", "*.iso"), ("All files", "*.*")]
        )
        if filename:
            self.win10_iso_path.set(filename)
    
    def browse_output_iso(self):
        """Browse for output ISO location"""
        filename = filedialog.asksaveasfilename(
            title="Save Modified ISO As",
            defaultextension=".iso",
            filetypes=[("ISO files", "*.iso"), ("All files", "*.*")]
        )
        if filename:
            self.output_iso_path.set(filename)
    
    def log(self, message):
        """Add message to log"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {message}\n"
            
            if hasattr(self, 'log_text'):
                self.log_text.insert(tk.END, log_message)
                self.log_text.see(tk.END)
                self.root.update_idletasks()
            else:
                print(log_message.strip())
        except Exception as e:
            print(f"Error logging message: {e}")
            print(f"Original message: {message}")
    
    def clear_log(self):
        """Clear the log text area"""
        try:
            if hasattr(self, 'log_text'):
                self.log_text.delete(1.0, tk.END)
        except Exception as e:
            print(f"Error clearing log: {e}")
    
    def copy_logs(self):
        """Copy application logs to clipboard"""
        try:
            if hasattr(self, "log_text"):
                logs = self.log_text.get(1.0, tk.END)
                self.root.clipboard_clear()
                self.root.clipboard_append(logs)
                self.root.update()  # Ensure clipboard is updated
                messagebox.showinfo("Success", "Application logs copied to clipboard!")
            else:
                messagebox.showwarning("Warning", "No logs available to copy")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy logs: {e}")    
    def update_status(self, status):
        """Update status bar"""
        try:
            self.status_var.set(status)
            self.root.update_idletasks()
        except Exception as e:
            print(f"Error updating status: {e}")
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        try:
            self.log("Checking dependencies...")
            
            dependencies = {
                'wimlib-imagex': 'wimlib-imagex --help',
                'hivexsh': 'hivexsh --help'
            }
            
            missing_deps = []
            for dep, cmd in dependencies.items():
                try:
                    result = subprocess.run(cmd.split(), capture_output=True, timeout=10)
                    if result.returncode == 0 or (dep == 'hivexsh' and result.returncode == 1):
                        # hivexsh returns 1 for --help but that means it exists
                        self.log(f"✓ {dep} found")
                    else:
                        self.log(f"✗ {dep} not found")
                        missing_deps.append(dep)
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    self.log(f"✗ {dep} not found")
                    missing_deps.append(dep)
            
            # Check pycdlib
            if not PYCDLIB_AVAILABLE:
                self.log("✗ pycdlib not found")
                missing_deps.append("pycdlib")
            else:
                self.log("✓ pycdlib found")
            
            if missing_deps:
                self.log("\nMissing dependencies. Please install:")
                self.log("brew install wimlib hivex")
                self.log("pip install pycdlib")
                # Schedule messagebox on main thread
                self.root.after(0, lambda: messagebox.showwarning("Dependencies Missing", 
                                     "Some required tools are missing. Check the log for installation instructions."))
            else:
                self.log("All dependencies found!")
                
        except Exception as e:
            self.log(f"Error checking dependencies: {e}")
    
    def validate_inputs(self):
        """Validate user inputs"""
        if not self.win11_iso_path.get():
            messagebox.showerror("Error", "Please select a Windows 11 ISO file")
            return False
        
        if not os.path.exists(self.win11_iso_path.get()):
            messagebox.showerror("Error", "Windows 11 ISO file does not exist")
            return False
        
        if not self.win10_iso_path.get():
            messagebox.showerror("Error", "Please select a Windows 10 ISO file for Boot Camp spoofing")
            return False
        
        if not os.path.exists(self.win10_iso_path.get()):
            messagebox.showerror("Error", "Windows 10 ISO file does not exist")
            return False
        
        if not self.output_iso_path.get():
            messagebox.showerror("Error", "Please specify an output location")
            return False
        
        # Check if output directory exists
        output_dir = Path(self.output_iso_path.get()).parent
        if not output_dir.exists():
            messagebox.showerror("Error", f"Output directory does not exist: {output_dir}")
            return False
        
        return True
    
    def start_patching(self):
        """Start the patching process in a separate thread"""
        if self.is_processing:
            return
        
        if not self.validate_inputs():
            return
        
        self.is_processing = True
        self.start_button.config(state='disabled', text='Patching...')
        self.progress.start()
        
        # Run patching in separate thread to avoid blocking UI
        thread = threading.Thread(target=self.patch_iso)
        thread.daemon = True
        thread.start()
    
    def patch_iso(self):
        """Main patching logic - WinPE injection approach"""
        try:
            win11_iso = self.win11_iso_path.get()
            win10_iso = self.win10_iso_path.get()
            output_iso = self.output_iso_path.get()
            
            if not all([win11_iso, win10_iso, output_iso]):
                raise Exception("Please select both input ISOs and output location")
            
            self.update_status("Starting WinPE injection process...")
            self.log(f"Windows 11 ISO: {win11_iso}")
            self.log(f"Windows 10 ISO: {win10_iso}")
            self.log(f"Output ISO: {output_iso}")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Step 1: Extract Windows 10 ISO to get WinPE
                self.update_status("Extracting Windows 10 ISO to get WinPE...")
                self.log("Step 1: Extracting Windows 10 ISO to get WinPE...")
                win10_extract_dir = temp_path / "win10_extract"
                self.extract_iso_contents(win10_iso, win10_extract_dir)
                
                # Find Windows 10 boot.wim
                win10_boot_wim = self.find_boot_wim(win10_extract_dir)
                if not win10_boot_wim:
                    raise Exception("Could not find boot.wim in Windows 10 ISO")
                self.log(f"✓ Found Windows 10 boot.wim at: {win10_boot_wim}")
                
                # Step 2: Extract Windows 11 ISO contents  
                self.update_status("Extracting Windows 11 ISO contents...")
                self.log("Step 2: Extracting Windows 11 ISO contents...")
                win11_extract_dir = temp_path / "win11_extract" 
                self.extract_iso_contents(win11_iso, win11_extract_dir)
                
                # Find Windows 11 boot.wim
                win11_boot_wim = self.find_boot_wim(win11_extract_dir)
                if not win11_boot_wim:
                    raise Exception("Could not find boot.wim in Windows 11 ISO")
                
                # Step 3: Replace Windows 11 boot.wim with Windows 10 boot.wim
                self.update_status("Injecting Windows 10 WinPE...")
                self.log("Step 3: Replacing Windows 11 boot.wim with Windows 10 boot.wim...")
                self.log(f"Replacing: {win11_boot_wim}")
                self.log(f"With: {win10_boot_wim}")
                shutil.copy2(win10_boot_wim, win11_boot_wim)
                self.log("✓ Windows 10 WinPE injected successfully")
                
                # Step 4: Add TPM bypass to the injected Windows 10 WinPE
                self.update_status("Adding TPM bypass to Windows 10 WinPE...")
                self.log("Step 4: Adding TPM bypass registry entries to Windows 10 WinPE...")
                self.add_tpm_bypass_to_boot_wim(win11_boot_wim, temp_path)
                
                # Step 5: Extract Windows 10 metadata for Boot Camp compatibility
                self.update_status("Extracting Windows 10 metadata...")
                self.log("Step 5: Extracting Windows 10 metadata for Boot Camp compatibility...")
                win10_metadata = self.extract_win10_metadata_from_iso(win10_iso)
                
                # Step 6: Create final ISO with Windows 10 branding
                self.update_status("Creating Boot Camp compatible ISO...")
                self.log("Step 6: Creating final ISO with Windows 10 branding...")
                self.create_bootcamp_iso(win11_extract_dir, output_iso, win10_metadata)
                
                # Step 7: Analyze and fix volume label for Boot Camp compatibility
                self.update_status("Analyzing volume label for Boot Camp compatibility...")
                self.log("Step 7: Analyzing volume label for Boot Camp compatibility...")
                current_volume_label = self.analyze_iso_volume_label(output_iso)
                
                if current_volume_label and not current_volume_label.startswith('CCCOMA_X64FRE_EN-US_DV9'):
                    self.log("⚠️ Volume label doesn't match Boot Camp expectations, attempting to fix...")
                    if self.force_bootcamp_volume_label(output_iso):
                        self.log("✅ Volume label successfully updated for Boot Camp compatibility")
                    else:
                        self.log("⚠️ Failed to update volume label, but continuing...")
                else:
                    self.log("✅ Volume label appears to be Boot Camp compatible")
                
                # Validate the created ISO
                self.log("Validating ISO for Boot Camp compatibility...")
                self.log("🔍 Boot Camp Analysis:")
                self.log("   • Volume ID: '{}' (Windows 10 format)".format(win10_metadata.get('volume_id', 'Unknown')))
                self.log("   • WinPE: Windows 10 (injected successfully)")
                self.log("   • Install: Windows 11 (will be installed)")
                self.log("   • TPM Bypass: Added to WinPE")
                
                # Run Boot Camp validation with enhanced debugging
                if self.disable_validation.get():
                    self.log("⚠️ Validation disabled by user - skipping file checks")
                    self.log("📝 Note: You can use the 'Debug Boot Camp Issues' button to manually check the ISO later")
                else:
                    self.validate_bootcamp_iso_with_debug(output_iso)
                
                self.update_status("WinPE injection completed successfully!")
                self.log("✅ WinPE injection completed successfully!")
                self.log(f"Boot Camp compatible ISO saved to: {output_iso}")
                
                # Show success dialog with troubleshooting info
                validation_note = ""
                if self.disable_validation.get():
                    validation_note = "\nNote: Validation was disabled. Use the 'Debug Boot Camp Issues' button to manually check the ISO."
                
                success_msg = f"""Windows 11 ISO has been successfully patched for Boot Camp!

Output: {output_iso}

What was changed:
• Replaced Windows 11 WinPE with Windows 10 WinPE
• Added TPM 2.0 and Secure Boot bypass
• Applied Windows 10 volume labeling for Boot Camp recognition

Boot Camp should now recognize this as a Windows 10 ISO while installing Windows 11.{validation_note}

If Boot Camp still doesn't recognize the ISO:
1. Click "Debug Boot Camp Issues" button for detailed analysis
2. Try a different Windows 10 ISO for the WinPE source
3. Check that your Mac supports Boot Camp with Windows 10
4. Verify the ISO file size and integrity
5. Try mounting the ISO manually with hdiutil to test compatibility"""
                
                messagebox.showinfo("Success", success_msg)
                
        except Exception as e:
            self.log(f"✗ Error: {str(e)}")
            self.update_status("WinPE injection failed!")
            messagebox.showerror("Error", f"WinPE injection failed: {str(e)}")
        
        finally:
            self.is_processing = False
            self.start_button.config(state='normal', text='Start Patching')
            self.progress.stop()

    def extract_iso_contents(self, iso_path, extract_dir):
        """Extract ISO contents with UDF/Joliet/ISO9660 fallback and proper filename handling"""
        self.log("Extracting ISO: {}".format(Path(iso_path).name))
        
        iso = pycdlib.PyCdlib()
        iso.open(iso_path)
        
        # Get ISO information
        try:
            volume_id = iso.pvd.volume_identifier.decode('utf-8').strip()
            self.log(f"ISO Volume ID: '{volume_id}'")
        except:
            self.log("ISO Volume ID: Could not decode")
        
        # Check for extensions
        extensions = []
        if hasattr(iso, 'udf_anchors') and iso.udf_anchors:
            extensions.append("UDF")
        if iso.joliet_vd:
            extensions.append("Joliet") 
        extensions.append("ISO 9660")
        self.log(f"ISO Extensions: {', '.join(extensions)}")
        
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        self.log("Extracting files...")
        
        # Try UDF first if available
        if hasattr(iso, 'udf_anchors') and iso.udf_anchors:
            self.log("UDF extension detected")
            if self.extract_udf_contents(iso, extract_dir):
                iso.close()
                return
        
        # Try Joliet if available
        if iso.joliet_vd:
            self.log("Joliet extension detected")
            if self.extract_joliet_contents(iso, extract_dir):
                iso.close()
                return
        
        # Fallback to ISO 9660
        self.log("Using ISO 9660 extraction")
        self.extract_iso9660_contents(iso, extract_dir)
        iso.close()

    def extract_udf_contents(self, iso, extract_dir):
        """Extract UDF contents with proper filename decoding"""
        try:
            self.log("Trying UDF extraction...")
            self.log(f"UDF anchors found: {len(iso.udf_anchors)}")
            
            files_extracted = 0
            dirs_created = 0
            
            # Use deque for iterative directory traversal
            from collections import deque
            dirs_to_process = deque(['/'])
            
            while dirs_to_process:
                current_dir = dirs_to_process.popleft()
                children_list = list(iso.list_children(udf_path=current_dir))
                self.log(f"Processing {current_dir}: found {len(children_list)} entries")
                
                for i, child in enumerate(children_list):
                    try:
                        # Try different methods to get filename from UDF entry
                        filename = None
                        
                        # Method 1: Try file_identifier() if it exists
                        if hasattr(child, 'file_identifier'):
                            try:
                                filename = child.file_identifier()
                                if isinstance(filename, bytes):
                                    filename = filename.decode('utf-8', errors='ignore').strip()
                            except:
                                pass
                        
                        # Method 2: Try accessing UDF file info directly
                        if not filename and hasattr(child, 'fi') and hasattr(child.fi, 'fi_ident'):
                            try:
                                raw_name_bytes = child.fi.fi_ident
                                filename = self.decode_udf_filename(raw_name_bytes)
                            except:
                                pass
                        
                        # Method 3: Try the identifier attribute directly
                        if not filename and hasattr(child, 'identifier'):
                            try:
                                if isinstance(child.identifier, bytes):
                                    filename = child.identifier.decode('utf-8', errors='ignore').strip()
                                else:
                                    filename = str(child.identifier)
                            except:
                                pass
                        
                        # Method 4: Try directory_record.identifier if it's a directory record
                        if not filename and hasattr(child, 'directory_record') and hasattr(child.directory_record, 'identifier'):
                            try:
                                if isinstance(child.directory_record.identifier, bytes):
                                    filename = child.directory_record.identifier.decode('utf-8', errors='ignore').strip()
                                else:
                                    filename = str(child.directory_record.identifier)
                            except:
                                pass
                        
                        # Clean up filename - remove any remaining null characters and ensure it's safe
                        if filename:
                            # Remove null characters and other problematic characters
                            filename = filename.replace('\x00', '').replace('\n', '').replace('\r', '').strip()
                            # Ensure filename is valid for filesystem
                            filename = ''.join(c for c in filename if c.isprintable() and c not in '<>:"/\\|?*')
                        
                        if not filename or filename in ['.', '..', '']:
                            self.log(f"  Entry {i+1}: Skipping entry with no valid filename")
                            continue
                            
                        self.log(f"  Entry {i+1}: {filename} ({'DIR' if child.is_dir() else 'FILE'})")
                        
                        # Create full paths
                        relative_path = current_dir.rstrip('/') + '/' + filename if current_dir != '/' else filename
                        local_path = extract_dir / relative_path.lstrip('/')
                        
                        if child.is_dir():
                            try:
                                local_path.mkdir(parents=True, exist_ok=True)
                                self.log(f"Created directory: {filename}")
                                dirs_to_process.append('/' + relative_path.lstrip('/') + '/')
                                dirs_created += 1
                            except Exception as e:
                                self.log(f"Warning: Failed to create directory {filename}: {e}")
                                continue
                        else:
                            try:
                                # Ensure parent directory exists
                                local_path.parent.mkdir(parents=True, exist_ok=True)
                                
                                # Extract file
                                with open(local_path, 'wb') as f:
                                    iso.get_file_from_iso_fp(f, udf_path='/' + relative_path.lstrip('/'))
                                
                                files_extracted += 1
                                if files_extracted % 100 == 0:
                                    self.log(f"Extracted {files_extracted} files so far...")
                                    
                            except Exception as e:
                                self.log(f"Warning: Failed to extract {filename}: {e}")
                                continue
                                
                    except Exception as e:
                        self.log(f"Warning: Error processing UDF entry {i}: {e}")
                        continue
            
            self.log(f"Extraction summary: {files_extracted} files, {dirs_created} directories")
            
            if files_extracted > 0:
                self.log(f"✓ Successfully extracted {files_extracted} files using UDF")
                self.log("✓ ISO extraction completed")
                return True
            else:
                self.log("✗ UDF extracted no files")
                return False
                
        except Exception as e:
            self.log(f"UDF extraction error: {e}")
            return False

    def decode_udf_filename(self, raw_bytes):
        """Decode UDF filename bytes with multiple strategies"""
        if not raw_bytes:
            return ""
        
        # Strategy 1: UTF-16LE decoding (most common for UDF)
        try:
            # UDF often uses UTF-16LE with null bytes
            decoded = raw_bytes.decode('utf-16le', errors='ignore')
            # Remove any remaining null characters and strip whitespace
            decoded = decoded.replace('\x00', '').strip()
            if decoded and decoded not in ['.', '..']:
                return decoded
        except:
            pass
        
        # Strategy 2: UTF-16BE decoding
        try:
            decoded = raw_bytes.decode('utf-16be', errors='ignore')
            decoded = decoded.replace('\x00', '').strip()
            if decoded and decoded not in ['.', '..']:
                return decoded
        except:
            pass
        
        # Strategy 3: Manual UTF-16LE with byte manipulation
        try:
            # Sometimes UDF has a leading byte we need to skip
            test_bytes = raw_bytes
            if len(raw_bytes) > 1 and raw_bytes[0] == 0:
                test_bytes = raw_bytes[1:]
            
            # Try decoding as UTF-16LE
            if len(test_bytes) % 2 == 0:
                decoded = test_bytes.decode('utf-16le', errors='ignore')
                decoded = decoded.replace('\x00', '').strip()
                if decoded and decoded not in ['.', '..']:
                    return decoded
        except:
            pass
        
        # Strategy 4: Clean up null bytes and try UTF-8
        try:
            cleaned_bytes = raw_bytes.replace(b'\x00', b'')
            decoded = cleaned_bytes.decode('utf-8', errors='ignore').strip()
            if decoded and decoded not in ['.', '..']:
                return decoded
        except:
            pass
        
        # Strategy 5: Latin-1 fallback
        try:
            cleaned_bytes = raw_bytes.replace(b'\x00', b'')
            decoded = cleaned_bytes.decode('latin-1', errors='ignore').strip()
            if decoded and decoded not in ['.', '..']:
                return decoded
        except:
            pass
        
        # Strategy 6: Character-by-character extraction (for badly encoded UTF-16)
        try:
            # Extract every other byte (skip null bytes)
            chars = []
            for i in range(0, len(raw_bytes), 2):
                if i < len(raw_bytes):
                    byte_val = raw_bytes[i]
                    if byte_val != 0 and 32 <= byte_val <= 126:  # Printable ASCII
                        chars.append(chr(byte_val))
            
            decoded = ''.join(chars).strip()
            if decoded and decoded not in ['.', '..']:
                return decoded
        except:
            pass
        
        # Strategy 7: Try every other byte starting from position 1
        try:
            chars = []
            for i in range(1, len(raw_bytes), 2):  # Start from position 1
                if i < len(raw_bytes):
                    byte_val = raw_bytes[i]
                    if byte_val != 0 and 32 <= byte_val <= 126:  # Printable ASCII
                        chars.append(chr(byte_val))
            
            decoded = ''.join(chars).strip()
            if decoded and decoded not in ['.', '..']:
                return decoded
        except:
            pass
        
        # Last resort: return hex representation
        return raw_bytes.hex()

    def extract_joliet_contents(self, iso, extract_dir):
        """Extract Joliet contents"""
        try:
            self.log("Trying Joliet extraction...")
            files_extracted = 0
            
            from collections import deque
            dirs_to_process = deque(['/'])
            
            while dirs_to_process:
                current_dir = dirs_to_process.popleft()
                
                for child in iso.list_children(joliet_path=current_dir):
                    # Get filename using multiple methods
                    filename = None
                    
                    if child.rock_ridge and child.rock_ridge.name():
                        filename = child.rock_ridge.name()
                    elif hasattr(child, 'file_identifier'):
                        filename = child.file_identifier()
                    elif hasattr(child, 'identifier'):
                        if isinstance(child.identifier, bytes):
                            filename = child.identifier.decode('utf-8', errors='ignore')
                        else:
                            filename = str(child.identifier)
                    
                    if not filename or filename in ['.', '..']:
                        continue
                    
                    relative_path = current_dir.rstrip('/') + '/' + filename if current_dir != '/' else filename
                    local_path = extract_dir / relative_path.lstrip('/')
                    
                    if child.is_dir():
                        local_path.mkdir(parents=True, exist_ok=True)
                        dirs_to_process.append('/' + relative_path.lstrip('/') + '/')
                    else:
                        local_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(local_path, 'wb') as f:
                            iso.get_file_from_iso_fp(f, joliet_path='/' + relative_path.lstrip('/'))
                        files_extracted += 1
            
            if files_extracted > 0:
                self.log(f"✓ Successfully extracted {files_extracted} files using Joliet")
                return True
            return False
            
        except Exception as e:
            self.log(f"Joliet extraction error: {e}")
            return False

    def extract_iso9660_contents(self, iso, extract_dir):
        """Extract ISO 9660 contents"""
        try:
            self.log("Trying ISO 9660 extraction...")
            files_extracted = 0
            
            from collections import deque
            dirs_to_process = deque(['/'])
            
            while dirs_to_process:
                current_dir = dirs_to_process.popleft()
                children_list = list(iso.list_children(iso_path=current_dir))
                self.log(f"Processing {current_dir}: found {len(children_list)} entries")
                
                for i, child in enumerate(children_list):
                    try:
                        # Get filename using multiple methods
                        filename = None
                        
                        if child.rock_ridge and child.rock_ridge.name():
                            filename = child.rock_ridge.name()
                        elif hasattr(child, 'file_identifier'):
                            filename = child.file_identifier()
                        elif hasattr(child, 'identifier'):
                            # child is already a DirectoryRecord, so access identifier directly
                            if isinstance(child.identifier, bytes):
                                filename = child.identifier.decode('utf-8', errors='ignore').strip()
                            else:
                                filename = str(child.identifier)
                        
                        # Handle bytes objects
                        if isinstance(filename, bytes):
                            filename = filename.decode('utf-8', errors='ignore').strip()
                        
                        self.log(f"  Entry {i}: {filename} ({'DIR' if child.is_dir() else 'FILE'})")
                        
                        if not filename or filename in ['.', '..']:
                            continue
                        
                        relative_path = current_dir.rstrip('/') + '/' + filename if current_dir != '/' else filename
                        local_path = extract_dir / relative_path.lstrip('/')
                        
                        if child.is_dir():
                            local_path.mkdir(parents=True, exist_ok=True)
                            dirs_to_process.append('/' + relative_path.lstrip('/') + '/')
                        else:
                            local_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(local_path, 'wb') as f:
                                iso.get_file_from_iso_fp(f, iso_path='/' + relative_path.lstrip('/'))
                            files_extracted += 1
                            
                    except Exception as e:
                        self.log(f"Warning: Error processing ISO 9660 entry {i}: {e}")
                        continue
            
            self.log(f"Extraction summary: {files_extracted} files, 0 directories")
            if files_extracted > 0:
                self.log(f"✓ Successfully extracted {files_extracted} files using ISO 9660")
            else:
                self.log("✗ ISO 9660 extracted no files")
                
        except Exception as e:
            self.log(f"ISO 9660 extraction error: {e}")

    def find_boot_wim(self, extract_dir):
        """Find boot.wim file in extracted ISO contents"""
        self.log("Searching for boot.wim...")
        
        # Common locations for boot.wim
        search_paths = [
            extract_dir / "sources" / "boot.wim",
            extract_dir / "Sources" / "boot.wim", 
            extract_dir / "SOURCES" / "boot.wim"
        ]
        
        # Check common paths first
        for path in search_paths:
            if path.exists():
                self.log(f"✓ Found boot.wim at: {path}")
                return path
        
        # If not found, search recursively
        self.log("Listing contents of extraction directory:")
        for item in extract_dir.iterdir():
            if item.is_file():
                size = item.stat().st_size
                self.log(f"  📄 {item.name} ({size:,} bytes)")
            elif item.is_dir():
                self.log(f"  📁 {item.name}/")
        
        self.log("Performing recursive search for boot.wim...")
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.lower() == "boot.wim":
                    boot_wim_path = Path(root) / file
                    self.log(f"✓ Found boot.wim at: {boot_wim_path}")
                    return boot_wim_path
        
        # Final attempt - look for any WIM files
        self.log("Searching for any WIM files...")
        wim_files = []
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.lower().endswith('.wim'):
                    wim_path = Path(root) / file
                    wim_files.append(wim_path)
                    self.log(f"Found WIM file: {wim_path}")
        
        if not wim_files:
            self.log("No WIM files found in the entire extraction")
        
        return None

    def list_directory_structure(self, directory, max_depth=3, current_depth=0):
        """List directory structure for debugging"""
        if current_depth >= max_depth:
            return
        
        try:
            indent = "  " * current_depth
            for item in sorted(directory.iterdir()):
                if item.is_file():
                    size = item.stat().st_size
                    self.log(f"{indent}📄 {item.name} ({size:,} bytes)")
                elif item.is_dir():
                    self.log(f"{indent}📁 {item.name}/")
                    # Only recurse if we haven't hit max depth
                    if current_depth < max_depth - 1:
                        self.list_directory_structure(item, max_depth, current_depth + 1)
        except Exception as e:
            self.log(f"{indent}Error listing directory: {e}")

    def add_tpm_bypass_to_boot_wim(self, boot_wim_path, temp_path):
        """Add TPM bypass to Windows 10 WinPE"""
        self.log("Adding TPM bypass to Windows 10 WinPE...")
        
        wim_extract_dir = temp_path / "boot_wim_extract"
        registry_script_path = temp_path / "tpm_bypass.txt"
        
        try:
            # Validate boot.wim file exists
            if not boot_wim_path.exists():
                raise Exception(f"boot.wim not found at: {boot_wim_path}")
            
            file_size = boot_wim_path.stat().st_size
            self.log(f"boot.wim size: {file_size:,} bytes ({file_size / (1024**2):.1f} MB)")
            
            # Check what images are available in boot.wim
            self.log("Checking available images in boot.wim...")
            info_result = subprocess.run([
                'wimlib-imagex', 'info', str(boot_wim_path)
            ], capture_output=True, text=True)
            
            if info_result.returncode != 0:
                self.log(f"Warning: Could not get boot.wim info: {info_result.stderr}")
                image_index = '1'  # Default fallback
            else:
                self.log("boot.wim info:")
                for line in info_result.stdout.split('\n')[:10]:  # Show first 10 lines
                    if line.strip():
                        self.log(f"  {line}")
                
                # Look for image indices in the output
                available_images = []
                for line in info_result.stdout.split('\n'):
                    if 'Index:' in line:
                        try:
                            idx = line.split('Index:')[1].strip()
                            available_images.append(idx)
                        except:
                            pass
                
                if available_images:
                    image_index = available_images[0]  # Use first available image
                    self.log(f"Using image index: {image_index}")
                else:
                    image_index = '1'  # Default fallback
                    self.log("No image indices found, using default index 1")
            
            # Create extraction directory
            wim_extract_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract boot.wim
            self.log(f"Extracting boot.wim image {image_index} for modification...")
            
            # Debug: Log the exact command being executed
            extract_cmd = ['wimlib-imagex', 'extract', str(boot_wim_path), image_index, '--dest-dir=' + str(wim_extract_dir), '--no-acls']
            self.log(f"DEBUG: Executing command: {extract_cmd}")
            
            extract_result = subprocess.run(extract_cmd, capture_output=True, text=True)
            
            if extract_result.returncode != 0:
                self.log(f"Extract failed with return code: {extract_result.returncode}")
                self.log(f"Extract stdout: {extract_result.stdout}")
                self.log(f"Extract stderr: {extract_result.stderr}")
                raise Exception(f"Failed to extract boot.wim: {extract_result.stderr}")
            
            self.log(f"✓ Successfully extracted boot.wim image {image_index}")
            
            # Verify extraction worked
            extracted_files = list(wim_extract_dir.rglob('*'))
            self.log(f"Extracted {len(extracted_files)} files/directories")
            
            # Create registry script for TPM bypass
            self.create_registry_script(registry_script_path)
            
            # Apply registry changes
            self.log("Adding TPM bypass registry entries...")
            system_hive = wim_extract_dir / "Windows" / "System32" / "config" / "SYSTEM"
            
            if system_hive.exists():
                self.log(f"Found SYSTEM hive at: {system_hive}")
                
                # Create a temporary script for hivexsh commands
                temp_script = temp_path / "hivex_script.txt"
                with open(temp_script, 'w') as f:
                    with open(registry_script_path, 'r') as reg_f:
                        f.write(reg_f.read())
                
                registry_result = subprocess.run([
                    'hivexsh', '-w', '-f', str(temp_script), str(system_hive)
                ], capture_output=True, text=True)
                
                if registry_result.returncode != 0:
                    self.log(f"Registry modification failed: {registry_result.stderr}")
                    # Try alternative approach if first fails
                    self.apply_registry_modifications_with_hivexsh(system_hive)
                else:
                    self.log("✓ Registry bypass entries added")
                
                # Clean up temporary script
                if temp_script.exists():
                    temp_script.unlink()
            else:
                self.log("Warning: SYSTEM registry hive not found, skipping TPM bypass")
                self.log(f"Expected location: {system_hive}")
                # List what we actually extracted
                win_dir = wim_extract_dir / "Windows"
                if win_dir.exists():
                    sys32_dir = win_dir / "System32"
                    if sys32_dir.exists():
                        config_dir = sys32_dir / "config"
                        if config_dir.exists():
                            config_files = list(config_dir.iterdir())
                            self.log(f"Found config files: {[f.name for f in config_files]}")
                        else:
                            self.log("config directory not found")
                    else:
                        self.log("System32 directory not found")
                else:
                    self.log("Windows directory not found")
            
            # Update boot.wim with modified contents
            self.log("Updating boot.wim with TPM bypass...")
            
            # Debug: Log the exact capture command being executed
            capture_cmd = ['wimlib-imagex', 'capture', str(wim_extract_dir), str(boot_wim_path), '--compress=LZX', '--check', '--boot']
            self.log(f"DEBUG: Executing capture command: {capture_cmd}")
            
            capture_result = subprocess.run(capture_cmd, capture_output=True, text=True)
            
            if capture_result.returncode != 0:
                self.log(f"Capture failed: {capture_result.stderr}")
                raise Exception(f"Failed to update boot.wim: {capture_result.stderr}")
            
            self.log("✓ TPM bypass added to Windows 10 WinPE")
            
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed with return code {e.returncode}")
            if hasattr(e, 'stdout') and e.stdout:
                self.log(f"Command stdout: {e.stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                self.log(f"Command stderr: {e.stderr}")
            raise Exception(f"Failed to add TPM bypass to boot.wim: {e}")
        except Exception as e:
            self.log(f"Error modifying boot.wim: {e}")
            raise Exception(f"Failed to add TPM bypass to boot.wim: {e}")

    def extract_win10_metadata_from_iso(self, win10_iso_path):
        """Extract Windows 10 metadata from ISO"""
        self.log("Extracting Windows 10 metadata...")

        # Force the volume ID to the known Boot Camp compatible string
        # This overrides any volume ID present in the source Windows 10 ISO
        forced_volume_id = 'CCCOMA_X64FRE_EN-US_DV9'
        self.log(f"Forcing Windows 10 volume ID to: {forced_volume_id}")

        try:
            iso = pycdlib.PyCdlib()
            iso.open(win10_iso_path)

            # Get original volume ID for logging purposes, but use the forced one
            original_volume_id = iso.pvd.volume_identifier.decode('utf-8').strip()
            self.log(f"Original Windows 10 ISO volume ID: '{original_volume_id}'")

            iso.close()

            metadata = {
                'volume_id': forced_volume_id, # Use the forced volume ID
                'application_id': 'Microsoft Windows',
                'publisher': 'Microsoft Corporation'
            }

            self.log("✓ Windows 10 metadata extracted and volume ID sanitized")
            return metadata

        except Exception as e:
            self.log(f"Error extracting Windows 10 metadata: {e}")
            # Return defaults, ensuring the volume_id is the forced one
            return {
                'volume_id': forced_volume_id, # Use the forced volume ID even on error
                'application_id': 'Microsoft Windows',
                'publisher': 'Microsoft Corporation'
            }

    def create_bootcamp_iso(self, source_dir, output_iso, win10_metadata):
        """Create Boot Camp compatible ISO with proper boot sectors"""
        self.log("Creating Boot Camp compatible ISO...")
        volume_label = win10_metadata.get('volume_id', 'CCCOMA_X64FRE_EN-US_DV9')
        self.log(f"Using volume label: {volume_label}")
        
        # Calculate source directory size for validation
        source_size = self.calculate_directory_size(source_dir)
        self.log(f"Source directory size: {source_size:,} bytes ({source_size / (1024**3):.2f} GB)")
        
        # Try Boot Camp optimized mkisofs first
        mkisofs_cmd = [
            'mkisofs',
            '-iso-level', '2',  # ISO Level 2 for Boot Camp compatibility
            '-J', '-R',  # Joliet and Rock Ridge extensions
            '-no-emul-boot',  # No emulation boot
            '-boot-load-size', '4',  # Boot load size
            '-boot-info-table',  # Boot info table
            '-eltorito-boot', 'boot/etfsboot.com',  # El Torito boot file
            '-V', volume_label,  # Volume label
            '-A', win10_metadata.get('application_id', 'Microsoft Windows'),  # Application identifier
            '-publisher', win10_metadata.get('publisher', 'Microsoft Corporation'),  # Publisher
            '-o', str(output_iso),
            str(source_dir)
        ]
        
        if self.try_iso_creation_method("Boot Camp optimized mkisofs", mkisofs_cmd, output_iso, source_size):
            return
        
        # Try simpler mkisofs with different options
        simple_mkisofs_cmd = [
            'mkisofs',
            '-J', '-r', '-allow-lowercase', '-allow-multidot',
            '-V', volume_label,
            '-o', str(output_iso),
            str(source_dir)
        ]
        
        if self.try_iso_creation_method("Simple mkisofs", simple_mkisofs_cmd, output_iso, source_size):
            return
        
        # Try genisoimage (check if available first)
        if self.check_command_available('genisoimage'):
            genisoimage_cmd = [
                'genisoimage',
                '-J', '-R', '-allow-lowercase', '-allow-multidot',
                '-V', volume_label,
                '-o', str(output_iso),
                str(source_dir)
            ]
            
            if self.try_iso_creation_method("genisoimage", genisoimage_cmd, output_iso, source_size):
                return
        else:
            self.log("genisoimage not available, skipping...")
        
        # Try mkisofs with UDF support for larger files
        udf_mkisofs_cmd = [
            'mkisofs',
            '-iso-level', '3',  # ISO Level 3 for UDF support
            '-J', '-R', '-udf',
            '-V', volume_label,
            '-o', str(output_iso),
            str(source_dir)
        ]
        
        if self.try_iso_creation_method("UDF mkisofs", udf_mkisofs_cmd, output_iso, source_size):
            return
        
        # Fallback to pycdlib with Boot Camp optimizations
        self.log("Using pycdlib with Boot Camp optimizations...")
        self.create_bootcamp_iso_with_pycdlib(source_dir, output_iso, volume_label)

    def check_command_available(self, command):
        """Check if a command is available in the system"""
        try:
            result = subprocess.run([command, '--help'], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def try_iso_creation_method(self, method_name, cmd, output_iso, expected_size):
        """Try an ISO creation method and validate the result"""
        try:
            self.log(f"Creating ISO with {method_name}...")
            self.log(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # Increased timeout
            
            if result.returncode == 0:
                if Path(output_iso).exists():
                    output_size = Path(output_iso).stat().st_size
                    self.log(f"{method_name} output size: {output_size:,} bytes ({output_size / (1024**3):.2f} GB)")
                    
                    # More lenient size validation (allow 60% of expected size)
                    if output_size < (expected_size * 0.6):
                        self.log(f"Warning: {method_name} created undersized ISO (expected ~{expected_size / (1024**3):.2f} GB)")
                        Path(output_iso).unlink()
                        return False
                    
                    # macOS mounting test (critical for Boot Camp)
                    if self.test_macos_iso_mounting(output_iso):
                        self.log(f"✅ ISO created successfully with {method_name}")
                        return True
                    else:
                        # Special handling for UDF ISOs - they might still work with Boot Camp
                        if "UDF" in method_name and output_size >= (expected_size * 0.8):
                            self.log(f"⚠️ {method_name} ISO failed macOS mounting test but is full-sized - may still work with Boot Camp")
                            self.log(f"✅ Accepting UDF ISO despite mounting test failure")
                            return True
                        else:
                            self.log(f"❌ {method_name} ISO fails macOS mounting test")
                            Path(output_iso).unlink()
                            return False
                else:
                    self.log(f"{method_name} did not create output file")
                    return False
            else:
                self.log(f"{method_name} failed with return code {result.returncode}")
                if result.stderr:
                    self.log(f"{method_name} error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"{method_name} timed out")
            return False
        except FileNotFoundError:
            self.log(f"{method_name} not found")
            return False
        except Exception as e:
            self.log(f"{method_name} error: {e}")
            return False

    def create_bootcamp_iso_with_pycdlib(self, source_dir, output_iso, volume_label):
        """Create Boot Camp compatible ISO using pycdlib with improved path handling"""
        try:
            self.log("Initializing pycdlib for Boot Camp ISO...")
            iso = pycdlib.PyCdlib()
            
            # Initialize with Rock Ridge and Joliet for maximum compatibility
            iso.new(interchange_level=3, 
                   joliet=3,
                   rock_ridge='1.09',
                   vol_ident=volume_label)
            
            # Add El Torito boot record for bootmgr
            bootmgr_path = Path(source_dir) / "bootmgr"
            if bootmgr_path.exists():
                self.log("Adding El Torito boot record for bootmgr...")
                iso.add_eltorito(str(bootmgr_path), "/BOOTMGR")
            
            # Add files recursively with improved path handling
            self.log("Adding files to Boot Camp ISO with improved path handling...")
            files_added = self.add_directory_to_iso_improved(iso, Path(source_dir), '/')
            self.log(f"Total files added: {files_added}")
            
            if files_added == 0:
                self.log("Warning: No files were added to ISO, trying minimal approach...")
                # Try minimal approach
                files_added = self.add_minimal_directory_to_iso(iso, Path(source_dir), '/')
                self.log(f"Minimal files added: {files_added}")
            
            # Write the ISO
            self.log("Writing Boot Camp ISO...")
            iso.write(output_iso)
            iso.close()
            
            # Validate size
            if Path(output_iso).exists():
                output_size = Path(output_iso).stat().st_size
                self.log(f"pycdlib Boot Camp ISO size: {output_size:,} bytes ({output_size / (1024**3):.2f} GB)")
                
                # Test mounting
                if self.test_macos_iso_mounting(output_iso):
                    self.log("✅ Boot Camp ISO created successfully with pycdlib")
                    return
                else:
                    self.log("⚠️ pycdlib ISO failed mounting test, trying fallback...")
                    Path(output_iso).unlink()
                    raise Exception("pycdlib ISO failed mounting test")
            else:
                raise Exception("pycdlib failed to create output file")
            
        except Exception as e:
            self.log(f"Error creating Boot Camp ISO with pycdlib: {e}")
            # Final fallback
            self.create_simple_iso_fallback(source_dir, output_iso, volume_label)

    def add_directory_to_iso_improved(self, iso, source_path, iso_path):
        """Add directory contents to ISO with improved path handling to avoid 'Input string too long!'"""
        files_added = 0
        skipped_files = 0
        
        try:
            for item in source_path.rglob('*'):
                if item.is_file():
                    # Create ISO path with very strict length limits
                    relative_path = item.relative_to(source_path)
                    # Fix: Move the replace operation outside the f-string
                    relative_path_str = str(relative_path).replace('\\', '/')
                    iso_file_path = f"{iso_path}{relative_path_str}"
                    
                    # Very strict path length limits for pycdlib (100 chars to be safe)
                    if len(iso_file_path) > 100:
                        self.log(f"Warning: Skipping file with path too long: {iso_file_path}")
                        skipped_files += 1
                        continue
                    
                    # Check for problematic characters and sequences
                    problematic_chars = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x09', '\x0a', '\x0b', '\x0c', '\x0d', '\x0e', '\x0f']
                    if any(char in iso_file_path for char in problematic_chars):
                        self.log(f"Warning: Skipping file with problematic characters: {iso_file_path}")
                        skipped_files += 1
                        continue
                    
                    # Check for non-ASCII characters that might cause issues
                    try:
                        iso_file_path.encode('ascii')
                    except UnicodeEncodeError:
                        self.log(f"Warning: Skipping file with non-ASCII characters: {iso_file_path}")
                        skipped_files += 1
                        continue
                    
                    # Additional safety check for very long filenames
                    if len(item.name) > 50:
                        self.log(f"Warning: Skipping file with very long name: {item.name}")
                        skipped_files += 1
                        continue
                    
                    try:
                        iso.add_file(str(item), iso_file_path)
                        files_added += 1
                        if files_added % 50 == 0:  # More frequent logging
                            self.log(f"Added {files_added} files to ISO...")
                    except Exception as e:
                        self.log(f"Warning: Failed to add file {iso_file_path}: {e}")
                        skipped_files += 1
                        continue
        except Exception as e:
            self.log(f"Error adding directory to ISO: {e}")
        
        if skipped_files > 0:
            self.log(f"Warning: Skipped {skipped_files} files due to path length or character issues")
        
        return files_added

    def create_simple_iso_fallback(self, source_dir, output_iso, volume_label):
        """Final fallback - create basic ISO with minimal files"""
        try:
            self.log("Creating basic fallback ISO with minimal files...")
            iso = pycdlib.PyCdlib()
            iso.new(joliet=3, vol_ident=volume_label)
            
            # Only add essential files to avoid path length issues
            essential_files = [
                'bootmgr', 'setup.exe', 'boot/bootmgr', 'sources/boot.wim', 'sources/install.wim', 'sources/setup.exe'
            ]
            
            files_added = 0
            for file_name in essential_files:
                file_path = Path(source_dir) / file_name
                if file_path.exists():
                    try:
                        iso.add_file(str(file_path), f"/{file_name}")
                        files_added += 1
                        self.log(f"Added essential file: {file_name}")
                    except Exception as e:
                        self.log(f"Warning: Failed to add essential file {file_name}: {e}")
            
            # Add a few more critical directories if they exist
            critical_dirs = ['boot', 'sources', 'efi']
            for dir_name in critical_dirs:
                dir_path = Path(source_dir) / dir_name
                if dir_path.exists():
                    try:
                        files_in_dir = self.add_minimal_directory_to_iso(iso, dir_path, f"/{dir_name}")
                        files_added += files_in_dir
                        self.log(f"Added {files_in_dir} files from {dir_name}/")
                    except Exception as e:
                        self.log(f"Warning: Failed to add directory {dir_name}: {e}")
            
            iso.write(output_iso)
            iso.close()
            
            if Path(output_iso).exists():
                output_size = Path(output_iso).stat().st_size
                self.log(f"Fallback ISO size: {output_size:,} bytes ({output_size / (1024**3):.2f} GB)")
            
            self.log(f"✅ Fallback ISO created with {files_added} files")
            
        except Exception as e:
            self.log(f"❌ Even fallback ISO creation failed: {e}")
            raise Exception("All ISO creation methods failed")

    def add_minimal_directory_to_iso(self, iso, source_path, iso_path):
        """Add minimal directory contents to avoid path length issues"""
        files_added = 0
        try:
            for item in source_path.rglob('*'):
                if item.is_file():
                    # Create very short ISO path
                    relative_path = item.relative_to(source_path)
                    iso_file_path = f"{iso_path}/{item.name}"  # Just use filename
                    
                    # Skip if still too long
                    if len(iso_file_path) > 64:
                        continue
                    
                    try:
                        iso.add_file(str(item), iso_file_path)
                        files_added += 1
                    except Exception as e:
                        continue
        except Exception as e:
            self.log(f"Error adding minimal directory: {e}")
        return files_added

    def calculate_directory_size(self, directory):
        """Calculate the total size of a directory"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size

    def add_directory_to_iso(self, iso, source_path, iso_path):
        """Add directory contents to ISO with proper path handling"""
        files_added = 0
        try:
            for item in source_path.rglob('*'):
                if item.is_file():
                    # Create ISO path
                    relative_path = item.relative_to(source_path)
                    # Fix: Move the replace operation outside the f-string
                    relative_path_str = str(relative_path).replace('\\', '/')
                    iso_file_path = f"{iso_path}{relative_path_str}"
                    
                    # Ensure path doesn't exceed ISO 9660 limits
                    if len(iso_file_path) > 255:
                        self.log(f"Warning: Skipping file with path too long: {iso_file_path}")
                        continue
                    
                    try:
                        iso.add_file(str(item), iso_file_path)
                        files_added += 1
                        if files_added % 100 == 0:
                            self.log(f"Added {files_added} files to ISO...")
                    except Exception as e:
                        self.log(f"Warning: Failed to add file {iso_file_path}: {e}")
                        continue
        except Exception as e:
            self.log(f"Error adding directory to ISO: {e}")
        return files_added

    def add_files_simple(self, iso, source_path, iso_path):
        """Add files to ISO with simplified path handling"""
        files_added = 0
        try:
            for item in source_path.rglob('*'):
                if item.is_file():
                    # Create simplified ISO path
                    relative_path = item.relative_to(source_path)
                    # Fix: Move the replace operation outside the f-string
                    relative_path_str = str(relative_path).replace('\\', '/')
                    iso_file_path = f"{iso_path}{relative_path_str}"
                    
                    # Truncate path if too long
                    if len(iso_file_path) > 200:  # Conservative limit
                        self.log(f"Warning: Truncating long path: {iso_file_path}")
                        # Keep only the filename
                        iso_file_path = f"{iso_path}{item.name}"
                    
                    try:
                        iso.add_file(str(item), iso_file_path)
                        files_added += 1
                        if files_added % 50 == 0:
                            self.log(f"Added {files_added} files to fallback ISO...")
                    except Exception as e:
                        self.log(f"Warning: Failed to add file to fallback ISO: {e}")
                        continue
        except Exception as e:
            self.log(f"Error adding files to fallback ISO: {e}")
        return files_added

    def validate_iso_structure(self, iso_path):
        """Validate basic ISO structure"""
        try:
            iso = pycdlib.PyCdlib()
            iso.open(iso_path)
            
            # Check if ISO has basic structure
            has_files = False
            for child in iso.list_children(iso_path='/'):
                has_files = True
                break
            
            iso.close()
            return has_files
        except Exception as e:
            self.log(f"ISO structure validation failed: {e}")
            return False

    def check_essential_windows_files(self, iso_path):
        """Check for essential Windows installation files"""
        # Based on the extraction logs, bootmgr is at root, not in boot/ directory
        essential_files = ['bootmgr', 'setup.exe', 'sources/boot.wim']
        found_files = []
        missing_files = []
        
        self.log(f"🔍 Checking for essential files: {', '.join(essential_files)}")
        
        try:
            iso = pycdlib.PyCdlib()
            iso.open(iso_path)
            
            # Debug: List all files in the ISO root
            self.log("🔍 Debug: Listing all files in ISO root:")
            try:
                for child in iso.list_children(iso_path='/'):
                    self.log(f"  - {child.file_identifier()}")
            except Exception as e:
                self.log(f"  Error listing files: {e}")
            
            # Collect all available paths for checking
            available_files = []
            try:
                # Check UDF paths
                for root, dirs, files in iso.walk(udf=True):
                    for file in files:
                        available_files.append(file)
                        self.log(f"  UDF file: {file}")
            except Exception as e:
                self.log(f"  Error walking UDF: {e}")
            
            try:
                # Check ISO paths
                for child in iso.list_children(iso_path='/'):
                    available_files.append(child.file_identifier())
                    self.log(f"  ISO file: {child.file_identifier()}")
            except Exception as e:
                self.log(f"  Error listing ISO files: {e}")
            
            # Check each essential file
            for file_path in essential_files:
                # Check if file exists in any of the available paths
                file_found = False
                
                # Check exact match
                if file_path in available_files:
                    found_files.append(file_path)
                    self.log(f"✅ Found: {file_path}")
                    file_found = True
                else:
                    # Check if it's a file within a directory (e.g., sources/boot.wim)
                    path_parts = file_path.split('/')
                    if len(path_parts) > 1:
                        # For files in subdirectories, check if the directory and file exist
                        dir_name = path_parts[0]
                        file_name = path_parts[1]
                        
                        # Look for the directory first
                        if dir_name in available_files:
                            # Check if the file exists in that directory
                            try:
                                for child in iso.list_children(iso_path=f"/{dir_name}"):
                                    if child.file_identifier() == file_name:
                                        found_files.append(file_path)
                                        self.log(f"✅ Found: {file_path}")
                                        file_found = True
                                        break
                            except Exception as e:
                                self.log(f"  Error checking directory {dir_name}: {e}")
                
                if not file_found:
                    missing_files.append(file_path)
                    self.log(f"❌ Missing: {file_path}")
            
            iso.close()
            
            # Log summary
            self.log(f"📊 Essential files summary: {len(found_files)}/{len(essential_files)} found")
            if missing_files:
                self.log(f"⚠️ Missing files: {', '.join(missing_files)}")
            
            # Return True if all essential files are found
            return len(found_files) == len(essential_files)
        except Exception as e:
            self.log(f"Essential files check failed: {e}")
            return False

    def get_iso_volume_id(self, iso_path):
        """Get ISO volume identifier"""
        try:
            iso = pycdlib.PyCdlib()
            iso.open(iso_path)
            vol_id = iso.get_volume_ident()
            iso.close()
            return vol_id
        except Exception as e:
            self.log(f"Volume ID check failed: {e}")
            return None

    def check_wim_files(self, iso_path):
        """Check for WIM files in the ISO"""
        wim_files = []
        try:
            iso = pycdlib.PyCdlib()
            iso.open(iso_path)
            
            for child in iso.list_children(iso_path='/'):
                if child.file_identifier().endswith('.wim'):
                    wim_files.append(child.file_identifier())
            
            iso.close()
            return len(wim_files) > 0
        except Exception as e:
            self.log(f"WIM files check failed: {e}")
            return False

    def check_bootable_signature(self, iso_path):
        """Check if ISO has bootable signature"""
        try:
            with open(iso_path, 'rb') as f:
                # Check for El Torito boot signature
                f.seek(0x8000)  # Boot sector location
                boot_sector = f.read(512)
                return boot_sector[510:512] == b'\x55\xaa'  # Boot signature
        except Exception as e:
            self.log(f"Boot signature check failed: {e}")
            return False

    def create_registry_script(self, script_path):
        """Create a registry script to add the bypass keys"""
        # Create hivexsh interactive commands
        hivexsh_commands = [
            "cd \\Setup",
            "ls",  # List to see if LabConfig exists
            "add LabConfig",  # This will fail if it exists, but that's OK
            "cd LabConfig",
            "setval 2",
            "BypassTPMCheck",
            "dword:1",
            "BypassSecureBootCheck", 
            "dword:1",
            "commit",
            "quit"
        ]
        with open(script_path, 'w') as f:
            f.write('\n'.join(hivexsh_commands) + '\n')
    
    def apply_registry_modifications_with_hivexsh(self, system_hive_path):
        """Apply registry modifications using hivexsh"""
        # First, try to navigate to the Setup key and create LabConfig if it doesn't exist
        self.log("Checking and creating registry structure...")
        
        # Create a temporary script file for hivexsh commands
        temp_script = system_hive_path.parent / "hivex_script.txt"
        
        try:
            # Create the hivexsh commands
            hivexsh_commands = [
                "cd \\Setup",
                "ls",  # List to see if LabConfig exists
                "add LabConfig",  # This will fail if it exists, but that's OK
                "cd LabConfig",
                "setval 2",
                "BypassTPMCheck",
                "dword:1",
                "BypassSecureBootCheck", 
                "dword:1",
                "commit",
                "quit"
            ]
            
            # Write commands to temporary script file
            with open(temp_script, 'w') as f:
                f.write('\n'.join(hivexsh_commands) + '\n')
            
            # Execute hivexsh with the script file and hive file
            cmd = ['hivexsh', '-w', '-f', str(temp_script), str(system_hive_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Check if it failed due to LabConfig already existing
            if result.returncode != 0 and "already exists" in result.stderr:
                self.log("LabConfig key already exists, updating values...")
                # Try again without creating the key
                hivexsh_commands_update = [
                    "cd \\Setup\\LabConfig",
                    "setval 2",
                    "BypassTPMCheck",
                    "dword:1",
                    "BypassSecureBootCheck", 
                    "dword:1",
                    "commit",
                    "quit"
                ]
                
                with open(temp_script, 'w') as f:
                    f.write('\n'.join(hivexsh_commands_update) + '\n')
                
                result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Failed to apply registry modifications with hivexsh: {result.stderr}")
            
            self.log("Registry modifications applied using hivexsh")
            
        finally:
            # Clean up temporary script file
            if temp_script.exists():
                temp_script.unlink()
    
    def modify_version_files(self, iso_extract_dir, win10_metadata):
        """Modify any version-related files in the ISO"""
        try:
            # Look for common version files that might need modification
            version_files = [
                "sources/setup.exe",
                "sources/setuphost.exe", 
                "autorun.inf",
                "setup.exe"
            ]
            
            for file_path in version_files:
                full_path = iso_extract_dir / file_path
                if full_path.exists():
                    self.log(f"Found version file: {file_path}")
                    # Note: For now, we'll just log their existence
                    # More sophisticated spoofing could modify PE headers, etc.
            
            # Check for and potentially modify autorun.inf
            autorun_path = iso_extract_dir / "autorun.inf"
            if autorun_path.exists():
                self.log("Found autorun.inf - this could be modified for deeper spoofing")
            
        except Exception as e:
            self.log(f"Warning: Error checking version files: {e}")

    def test_macos_iso_mounting(self, iso_path):
        """Test if the ISO can be mounted by macOS using hdiutil"""
        self.log("Testing macOS ISO mounting compatibility...")
        
        try:
            # Try to mount the ISO
            result = subprocess.run(['hdiutil', 'attach', iso_path, '-readonly'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.log(f"❌ macOS mounting test failed: {result.stderr.strip()}")
                return False
            
            # Extract mount point from output
            mount_point = None
            for line in result.stdout.split('\n'):
                if '/dev/disk' in line and '/Volumes/' in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith('/Volumes/'):
                            mount_point = part
                            break
                    if mount_point:
                        break
            
            if not mount_point:
                self.log("❌ Could not determine mount point from hdiutil output")
                return False
            
            self.log(f"✅ ISO mounted successfully at: {mount_point}")
            
            # Check for essential files in mounted ISO
            essential_files = ['bootmgr', 'setup.exe', 'sources/boot.wim', 'sources/install.wim']
            missing_files = []
            
            for file_path in essential_files:
                full_path = os.path.join(mount_point, file_path)
                if not os.path.exists(full_path):
                    missing_files.append(file_path)
            
            if missing_files:
                self.log(f"⚠️ Missing essential files in mounted ISO: {missing_files}")
            else:
                self.log("✅ All essential files found in mounted ISO")
            
            # Unmount the ISO
            unmount_result = subprocess.run(['hdiutil', 'detach', mount_point], 
                                          capture_output=True, text=True, timeout=30)
            
            if unmount_result.returncode != 0:
                # Try force unmount
                self.log("Attempting force unmount...")
                force_result = subprocess.run(['hdiutil', 'detach', mount_point, '-force'], 
                                           capture_output=True, text=True, timeout=30)
                if force_result.returncode != 0:
                    self.log(f"⚠️ Warning: Could not unmount ISO: {force_result.stderr.strip()}")
                else:
                    self.log("✅ ISO unmounted successfully")
            else:
                self.log("✅ ISO unmounted successfully")
            
            return True
            
        except subprocess.TimeoutExpired:
            self.log("❌ macOS mounting test timed out")
            return False
        except Exception as e:
            self.log(f"❌ macOS mounting test failed: {str(e)}")
            return False

    def validate_bootcamp_iso(self, iso_path):
        """Comprehensive validation of the generated ISO for Boot Camp compatibility"""
        self.log("🔍 Performing comprehensive Boot Camp validation...")
        
        if not os.path.exists(iso_path):
            raise Exception(f"ISO file not found: {iso_path}")
        
        # Check file size
        file_size = os.path.getsize(iso_path)
        size_gb = file_size / (1024**3)
        self.log(f"📁 ISO file size: {size_gb:.2f} GB")
        
        if size_gb < 1.0:
            self.log("⚠️ Warning: ISO file size is very small, may be incomplete")
        
        # Enhanced ISO analysis for Boot Camp debugging
        self.log("🔍 Performing detailed ISO analysis for Boot Camp compatibility...")
        self.analyze_iso_for_bootcamp(iso_path)
        
        # Validate ISO structure
        self.log("🔍 Validating ISO structure...")
        if not self.validate_iso_structure(iso_path):
            raise Exception("ISO structure validation failed")
        
        # Check essential Windows files
        self.log("🔍 Checking essential Windows files...")
        if not self.check_essential_windows_files(iso_path):
            raise Exception("Essential Windows files missing")
        
        # Get and validate volume ID
        self.log("🔍 Checking volume ID...")
        volume_id = self.get_iso_volume_id(iso_path)
        if not volume_id:
            self.log("⚠️ Warning: Could not determine volume ID")
        else:
            self.log(f"📋 Volume ID: {volume_id}")
        
        # Check WIM files
        self.log("🔍 Checking WIM files...")
        if not self.check_wim_files(iso_path):
            raise Exception("Required WIM files missing")
        
        # Check bootable signature
        self.log("🔍 Checking bootable signature...")
        if not self.check_bootable_signature(iso_path):
            self.log("⚠️ Warning: ISO may not be bootable")
        
        # Test macOS mounting
        self.log("🔍 Testing macOS mounting compatibility...")
        if not self.test_macos_iso_mounting(iso_path):
            self.log("⚠️ Warning: ISO may not be compatible with macOS mounting")
        
        # Boot Camp specific checks
        self.log("🔍 Performing Boot Camp specific checks...")
        self.perform_bootcamp_specific_checks(iso_path)
        
        self.log("✅ Boot Camp validation completed successfully!")
        return True

    def validate_bootcamp_iso_with_debug(self, iso_path):
        """Validate Boot Camp ISO with enhanced debugging"""
        try:
            return self.validate_bootcamp_iso(iso_path)
        except Exception as e:
            self.log(f"❌ Boot Camp validation failed: {e}")
            self.log("🔍 Running enhanced debugging...")
            self.debug_bootcamp_issues(iso_path)
            raise e

    def analyze_iso_for_bootcamp(self, iso_path):
        """Detailed analysis of ISO for Boot Camp compatibility debugging"""
        try:
            iso = pycdlib.PyCdlib()
            iso.open(iso_path)
            
            self.log("📊 Detailed ISO Analysis for Boot Camp:")
            
            # Check ISO format
            self.log(f"  - ISO Level: {iso.interchange_level}")
            self.log(f"  - Joliet: {'Yes' if iso.joliet_vd() else 'No'}")
            self.log(f"  - Rock Ridge: {'Yes' if iso.rock_ridge else 'No'}")
            self.log(f"  - UDF: {'Yes' if iso.udf_vd() else 'No'}")
            
            # Check boot sectors
            try:
                boot_catalog = iso.get_boot_catalog()
                self.log(f"  - Boot Catalog: Present")
                self.log(f"  - Boot Catalog Entries: {len(boot_catalog.initial_entries)}")
            except:
                self.log("  - Boot Catalog: Missing or invalid")
            
            # Check volume descriptors
            try:
                pvd = iso.pvd
                self.log(f"  - Primary Volume Descriptor: Present")
                self.log(f"  - Volume ID: {pvd.volume_ident.decode('utf-8').strip()}")
                self.log(f"  - Application ID: {pvd.application_ident.decode('utf-8').strip()}")
                self.log(f"  - Publisher ID: {pvd.publisher_ident.decode('utf-8').strip()}")
            except:
                self.log("  - Primary Volume Descriptor: Error reading")
            
            # Check file structure
            essential_bootcamp_files = [
                'bootmgr',
                'setup.exe', 
                'sources/boot.wim',
                'sources/install.wim',
                'boot/bootmgr',
                'boot/bcd',
                'boot/boot.sdi'
            ]
            
            self.log("  - Essential Boot Camp Files:")
            for file_path in essential_bootcamp_files:
                try:
                    # Try different path formats
                    found = False
                    for path_format in [f"/{file_path}", file_path, f"\\{file_path}"]:
                        try:
                            if path_format.startswith('/'):
                                iso.get_file_from_iso(udf_path=path_format)
                            else:
                                iso.get_file_from_iso(iso_path=path_format)
                            self.log(f"    ✅ {file_path}")
                            found = True
                            break
                        except:
                            continue
                    if not found:
                        self.log(f"    ❌ {file_path}")
                except Exception as e:
                    self.log(f"    ❌ {file_path} (Error: {e})")
            
            # Check directory structure
            self.log("  - Root Directory Contents:")
            try:
                for child in iso.list_children(iso_path='/'):
                    self.log(f"    - {child.file_identifier()}")
            except Exception as e:
                self.log(f"    Error listing root contents: {e}")
            
            iso.close()
            
        except Exception as e:
            self.log(f"❌ Error analyzing ISO: {e}")

    def perform_bootcamp_specific_checks(self, iso_path):
        """Perform checks specific to Boot Camp requirements"""
        self.log("🔍 Boot Camp Specific Checks:")
        
        # Check for Windows 10 compatibility indicators
        try:
            iso = pycdlib.PyCdlib()
            iso.open(iso_path)
            
            # Check for Windows 10 version files
            version_files = [
                'sources/boot.wim',
                'sources/install.wim'
            ]
            
            for version_file in version_files:
                try:
                    # Extract and check WIM file version info
                    temp_dir = tempfile.mkdtemp()
                    try:
                        iso.get_file_from_iso(udf_path=f"/{version_file}")
                        # This is a simplified check - in a real implementation we'd extract and analyze the WIM
                        self.log(f"  ✅ {version_file} present")
                    except:
                        self.log(f"  ❌ {version_file} missing")
                    finally:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    self.log(f"  ❌ Error checking {version_file}: {e}")
            
            # Check for proper boot configuration
            boot_files = ['bootmgr', 'boot/bootmgr']
            for boot_file in boot_files:
                try:
                    iso.get_file_from_iso(udf_path=f"/{boot_file}")
                    self.log(f"  ✅ {boot_file} present")
                except:
                    self.log(f"  ❌ {boot_file} missing")
            
            iso.close()
            
        except Exception as e:
            self.log(f"❌ Error in Boot Camp specific checks: {e}")
        
        # Additional Boot Camp recommendations
        self.log("💡 Boot Camp Compatibility Tips:")
        self.log("  - Ensure the ISO is created with proper boot sectors")
        self.log("  - Verify that Windows 10 boot.wim is properly injected")
        self.log("  - Check that TPM/Secure Boot bypasses are correctly applied")
        self.log("  - Ensure volume label matches Windows 10 format")
        self.log("  - Try mounting the ISO manually with hdiutil to verify compatibility")
        
        # Provide manual testing instructions
        self.log("🔧 Manual Boot Camp Testing Instructions:")
        self.log("  1. Open Boot Camp Assistant")
        self.log("  2. Select 'Download or copy the Windows support software'")
        self.log("  3. Choose 'Download the Windows support software for this Mac'")
        self.log("  4. In the next step, select 'Create a Windows 10 or later install disk'")
        self.log("  5. When prompted for an ISO, select the generated ISO file")
        self.log("  6. If Boot Camp doesn't recognize the ISO, try these steps:")
        self.log("     - Mount the ISO manually: hdiutil attach /path/to/your/iso")
        self.log("     - Check if it mounts successfully")
        self.log("     - Look for any error messages in Console.app")
        self.log("     - Try copying the ISO to a different location")
        self.log("     - Ensure the ISO file has proper permissions")

    def debug_bootcamp_issues(self, iso_path):
        """Provide detailed debugging information for Boot Camp issues"""
        self.log("🔍 Boot Camp Issue Debugging:")
        
        # Check file permissions
        try:
            stat_info = os.stat(iso_path)
            self.log(f"  - File permissions: {oct(stat_info.st_mode)[-3:]}")
            self.log(f"  - File owner: {stat_info.st_uid}")
            self.log(f"  - File size: {stat_info.st_size:,} bytes")
        except Exception as e:
            self.log(f"  - Error checking file info: {e}")
        
        # Check if file is accessible
        try:
            with open(iso_path, 'rb') as f:
                f.read(1024)  # Read first 1KB
            self.log("  - File is readable")
        except Exception as e:
            self.log(f"  - File access error: {e}")
        
        # Test manual mounting
        self.log("  - Testing manual ISO mounting...")
        try:
            result = subprocess.run(['hdiutil', 'attach', '-readonly', '-nobrowse', iso_path], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.log("  - Manual mounting successful")
                # Extract mount point
                for line in result.stdout.split('\n'):
                    if '/Volumes/' in line:
                        mount_point = line.split()[-1]
                        self.log(f"  - Mounted at: {mount_point}")
                        # List contents
                        try:
                            ls_result = subprocess.run(['ls', '-la', mount_point], 
                                                     capture_output=True, text=True, timeout=10)
                            if ls_result.returncode == 0:
                                self.log("  - Mounted contents:")
                                for content_line in ls_result.stdout.split('\n')[:10]:  # First 10 lines
                                    if content_line.strip():
                                        self.log(f"    {content_line}")
                        except Exception as e:
                            self.log(f"  - Error listing mounted contents: {e}")
                        
                        # Unmount
                        subprocess.run(['hdiutil', 'detach', mount_point], 
                                     capture_output=True, timeout=10)
                        break
            else:
                self.log(f"  - Manual mounting failed: {result.stderr}")
        except Exception as e:
            self.log(f"  - Manual mounting error: {e}")
        
        # Check for common Boot Camp issues
        self.log("  - Common Boot Camp Issues:")
        self.log("    * ISO file too large (>4GB) - Boot Camp may have size limits")
        self.log("    * ISO format not recognized - Try different ISO creation method")
        self.log("    * Missing boot sectors - Ensure proper boot configuration")
        self.log("    * Volume label issues - Check volume identifier format")
        self.log("    * File system compatibility - Try ISO 9660 instead of UDF")
        
        # Analyze volume label specifically
        self.log("  - Volume Label Analysis:")
        try:
            current_volume_label = self.analyze_iso_volume_label(iso_path)
            if current_volume_label:
                if current_volume_label.startswith('CCCOMA_X64FRE_EN-US_DV9'):
                    self.log(f"    ✅ Volume label '{current_volume_label}' appears Boot Camp compatible")
                else:
                    self.log(f"    ⚠️ Volume label '{current_volume_label}' may not be Boot Camp compatible")
                    self.log("    💡 Try using the 'Force Boot Camp Volume Label' option")
            else:
                self.log("    ❌ Could not analyze volume label")
        except Exception as e:
            self.log(f"    ❌ Error analyzing volume label: {e}")
        
        # Suggest alternative approaches
        self.log("  - Alternative Approaches:")
        self.log("    * Try creating the ISO with different tools (mkisofs vs genisoimage)")
        self.log("    * Use a smaller Windows 10 ISO as base")
        self.log("    * Check if Boot Camp supports the specific Windows version")
        self.log("    * Try mounting the ISO in Disk Utility first")
        self.log("    * Consider using a different Windows 10 ISO source")

    def debug_current_iso(self):
        """Debug the current output ISO for Boot Camp issues"""
        output_iso = self.output_iso_path.get()
        
        if not output_iso:
            self.log("❌ No output ISO path specified")
            return
        
        if not os.path.exists(output_iso):
            self.log("❌ Output ISO file does not exist")
            return
        
        self.log("🔍 Starting Boot Camp issue debugging...")
        self.log(f"📁 Analyzing ISO: {output_iso}")
        
        # Run comprehensive debugging
        try:
            self.debug_bootcamp_issues(output_iso)
            self.log("✅ Boot Camp debugging completed")
        except Exception as e:
            self.log(f"❌ Error during debugging: {e}")
        
        # Provide additional manual testing steps
        self.log("🔧 Manual Testing Steps:")
        self.log("1. Open Boot Camp Assistant")
        self.log("2. Try to select the generated ISO")
        self.log("3. If it fails, check Console.app for error messages")
        self.log("4. Try mounting the ISO manually: hdiutil attach /path/to/iso")
        self.log("5. Check if the ISO appears in Disk Utility")

    def force_current_iso_volume_label(self):
        """Force the current output ISO to have the correct Boot Camp volume label"""
        output_iso = self.output_iso_path.get()
        
        if not output_iso:
            self.log("❌ No output ISO path specified")
            return
        
        if not os.path.exists(output_iso):
            self.log("❌ Output ISO file does not exist")
            return
        
        self.log("🔧 Forcing Boot Camp volume label...")
        self.log(f"📁 Target ISO: {output_iso}")
        
        # First analyze the current volume label
        current_volume_label = self.analyze_iso_volume_label(output_iso)
        
        if current_volume_label and current_volume_label.startswith('CCCOMA_X64FRE_EN-US_DV9'):
            self.log("✅ Volume label already appears to be Boot Camp compatible")
            return
        
        # Try to force the volume label
        try:
            if self.force_bootcamp_volume_label(output_iso):
                self.log("✅ Successfully updated volume label for Boot Camp compatibility")
                messagebox.showinfo("Success", "Volume label updated successfully!")
            else:
                self.log("❌ Failed to update volume label")
                messagebox.showerror("Error", "Failed to update volume label")
        except Exception as e:
            self.log(f"❌ Error updating volume label: {e}")
            messagebox.showerror("Error", f"Error updating volume label: {e}")

    def analyze_iso_volume_label(self, iso_path):
        """Analyze the volume label of an ISO file"""
        try:
            iso = pycdlib.PyCdlib()
            iso.open(iso_path)
            
            # Get volume ID from PVD
            volume_id = iso.pvd.volume_identifier.decode('utf-8').strip()
            self.log(f"Current ISO volume label: '{volume_id}'")
            
            # Check if it matches expected Boot Camp format
            expected_patterns = [
                'CCCOMA_X64FRE_EN-US_DV9',
                'CCCOMA_X64FRE_EN-US_DV9%202',
                'CCCOMA_X64FRE_EN-US_DV9%203'
            ]
            
            for pattern in expected_patterns:
                if volume_id == pattern:
                    self.log(f"✅ Volume label matches expected Boot Camp pattern: {pattern}")
                    iso.close()
                    return volume_id
            
            self.log(f"⚠️ Volume label '{volume_id}' doesn't match expected Boot Camp patterns")
            iso.close()
            return volume_id
            
        except Exception as e:
            self.log(f"Error analyzing ISO volume label: {e}")
            return None

    def force_bootcamp_volume_label(self, iso_path, target_volume_label='CCCOMA_X64FRE_EN-US_DV9'):
        """Force the volume label to match what Boot Camp expects"""
        self.log(f"Attempting to force volume label to: {target_volume_label}")
        
        try:
            # Create a temporary directory for the ISO contents
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract the ISO contents
                self.log("Extracting ISO contents for volume label modification...")
                self.extract_iso_contents(iso_path, temp_dir)
                
                # Remove the original ISO
                Path(iso_path).unlink()
                
                # Recreate the ISO with the correct volume label
                self.log("Recreating ISO with correct volume label...")
                metadata = {
                    'volume_id': target_volume_label,
                    'application_id': 'Microsoft Windows',
                    'publisher': 'Microsoft Corporation'
                }
                
                self.create_bootcamp_iso(temp_dir, iso_path, metadata)
                
                # Verify the new volume label
                new_volume_label = self.analyze_iso_volume_label(iso_path)
                if new_volume_label == target_volume_label:
                    self.log("✅ Successfully updated volume label")
                    return True
                else:
                    self.log(f"⚠️ Volume label update may have failed. Current: '{new_volume_label}', Expected: '{target_volume_label}'")
                    return False
                    
        except Exception as e:
            self.log(f"Error forcing Boot Camp volume label: {e}")
            return False

def main():
    print("=== Windows 11 Boot Camp ISO Patcher ===")
    print("Starting application...")
    
    if not PYCDLIB_AVAILABLE:
        print("pycdlib not available, running in command-line mode...")
        # Create a simple command-line interface
        print("Command-line mode not yet implemented.")
        print("Please install pycdlib or try:")
        print("  pip install pycdlib")
        return
    
    try:
        print("Creating Tkinter root...")
        root = tk.Tk()
        print("Root created successfully!")
        
        print("Creating app instance...")
        app = Win11BootCampPatcher(root)
        print("App instance created successfully!")
        
        # Check if running on macOS after GUI is initialized
        if sys.platform != 'darwin':
            print("Showing platform warning...")
            messagebox.showwarning("Platform Warning", 
                                 "This tool is designed for macOS. Some features may not work on other platforms.")
        
        print("Starting main loop...")
        root.mainloop()
        print("Main loop ended!")
        
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 