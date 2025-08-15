#!/usr/bin/env python3
"""
Simple test script to verify ISO creation tools work correctly
"""

import subprocess
import tempfile
import os
from pathlib import Path

def test_iso_tools():
    """Test if ISO creation tools work correctly"""
    print("🔧 Testing ISO Creation Tools")
    print("=" * 40)
    
    # Create test directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_content"
        test_dir.mkdir()
        
        # Create some test files
        (test_dir / "test.txt").write_text("Hello, Boot Camp!")
        (test_dir / "bootmgr").write_bytes(b"FAKE_BOOTMGR" + b"\x00" * 2000)  # Fake bootmgr
        
        sources_dir = test_dir / "sources"
        sources_dir.mkdir()
        (sources_dir / "boot.wim").write_text("Fake WIM file")
        
        test_iso = Path(temp_dir) / "test.iso"
        
        # Test mkisofs
        print("\n📦 Testing mkisofs...")
        try:
            cmd = [
                'mkisofs',
                '-iso-level', '3',
                '-J', '-r',
                '-V', 'TEST_ISO',
                '-o', str(test_iso),
                str(test_dir)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                iso_size = test_iso.stat().st_size
                print(f"✅ mkisofs succeeded - created {iso_size:,} byte ISO")
                
                # Test if macOS can read it
                file_result = subprocess.run(['file', str(test_iso)], capture_output=True, text=True)
                if 'ISO 9660' in file_result.stdout:
                    print("✅ macOS recognizes the ISO format")
                else:
                    print(f"⚠️  Unexpected format: {file_result.stdout}")
                    
            else:
                print(f"❌ mkisofs failed: {result.stderr}")
                
        except FileNotFoundError:
            print("❌ mkisofs not found")
        except Exception as e:
            print(f"❌ mkisofs test error: {e}")
        
        # Test pycdlib
        print("\n🐍 Testing pycdlib...")
        try:
            import pycdlib
            
            iso = pycdlib.PyCdlib()
            iso.new(joliet=3, vol_ident='PYCDLIB_TEST')
            
            # Add test files
            iso.add_file(str(test_dir / "test.txt"), joliet_path="/test.txt")
            iso.add_file(str(test_dir / "bootmgr"), joliet_path="/bootmgr")
            
            # Try to add boot record
            try:
                iso.add_eltorito("/bootmgr", boot_load_size=4)
                print("✅ Added El Torito boot record")
            except Exception as e:
                print(f"⚠️  Could not add boot record: {e}")
            
            pycdlib_iso = Path(temp_dir) / "pycdlib_test.iso"
            iso.write(str(pycdlib_iso))
            iso.close()
            
            if pycdlib_iso.exists():
                iso_size = pycdlib_iso.stat().st_size
                print(f"✅ pycdlib succeeded - created {iso_size:,} byte ISO")
                
                # Test if it's readable
                file_result = subprocess.run(['file', str(pycdlib_iso)], capture_output=True, text=True)
                if 'ISO 9660' in file_result.stdout:
                    print("✅ pycdlib ISO format is valid")
                else:
                    print(f"⚠️  pycdlib format issue: {file_result.stdout}")
            else:
                print("❌ pycdlib failed to create ISO")
                
        except ImportError:
            print("❌ pycdlib not available")
        except Exception as e:
            print(f"❌ pycdlib test error: {e}")
        
        print("\n🏁 Test Summary:")
        print("- If mkisofs works: Your ISOs should be bootable and Boot Camp compatible")
        print("- If only pycdlib works: ISOs may work but might have bootability issues")
        print("- If both fail: You need to install missing dependencies")

if __name__ == "__main__":
    test_iso_tools()
