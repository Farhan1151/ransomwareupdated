import os
import string
import base64
import psutil
import time

class AutomatedDriveDecryptor:
    def __init__(self):
        # Create decryption mapping
        self.decryption_map = self._create_comprehensive_decryption_map()
        
    def _create_comprehensive_decryption_map(self):
        """Create decryption mapping that reverses the enhanced encryption"""
        base64_chars = list(string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/')
        symbols = list('!@#$%^&*()_-=+[]{}|;:,.<>?`~ ')
        all_chars = base64_chars + symbols
        
        shuffled_chars = all_chars.copy()
        
        import random
        random.seed(42)
        random.shuffle(shuffled_chars)
        
        mapping = {}
        for orig, enc in zip(all_chars, shuffled_chars):
            mapping[enc] = orig
        return mapping
    
    def get_available_drives(self):
        """Get list of available drives on the system excluding only C:"""
        drives = []
        try:
            if os.name == 'nt':  # Windows
                for partition in psutil.disk_partitions():
                    if 'cdrom' not in partition.opts:
                        drive_path = partition.mountpoint
                        # Exclude only C: drive, include D: and others
                        if drive_path.upper() not in ['C:\\']:
                            drives.append(drive_path)
            else:  # Linux/Mac
                for partition in psutil.disk_partitions():
                    if partition.fstype and partition.mountpoint:
                        drive_path = partition.mountpoint
                        # For non-Windows systems, exclude root and common system mounts
                        if drive_path not in ['/', '/boot', '/home']:
                            drives.append(drive_path)
        except:
            # Fallback method for Windows
            import string
            for letter in string.ascii_uppercase:
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path) and drive_path not in ['C:\\']:  # Only exclude C:
                    drives.append(drive_path)
        
        return drives
    
    def get_encrypted_files(self, start_path):
        """Recursively get all encrypted files from a drive/folder"""
        encrypted_files = []
        folders_scanned = 0
        
        try:
            for root, dirs, files in os.walk(start_path):
                folders_scanned += 1
                
                for file in files:
                    if file.endswith('.encrypted'):
                        file_path = os.path.join(root, file)
                        encrypted_files.append(file_path)
                        
        except Exception as e:
            print(f"    Error scanning {start_path}: {str(e)}")
        
        return encrypted_files, folders_scanned
    
    def decrypt_and_restore_file(self, encrypted_file_path):
        """Decrypt a file and restore it to original (automatically delete encrypted file)"""
        try:
            # Read encrypted file
            with open(encrypted_file_path, 'r', encoding='utf-8') as file:
                encrypted_content = file.read()
            
            # Parse headers
            lines = encrypted_content.split('\n')
            original_name = "decrypted_file"
            file_type = ""
            data_start_index = 0
            
            for i, line in enumerate(lines):
                if line.startswith("ORIGINAL_NAME:"):
                    original_name = line.replace("ORIGINAL_NAME:", "").strip()
                elif line.startswith("FILE_TYPE:"):
                    file_type = line.replace("FILE_TYPE:", "").strip()
                elif line.strip() == "DATA:":
                    data_start_index = i + 1
                    break
            
            # Get encrypted data
            actual_encrypted_content = '\n'.join(lines[data_start_index:])
            
            # Decrypt base64 string
            decrypted_base64 = self.decrypt_text(actual_encrypted_content)
            
            # Convert base64 back to binary
            binary_data = base64.b64decode(decrypted_base64)
            
            # Create original file path
            original_file_path = os.path.join(os.path.dirname(encrypted_file_path), original_name)
            
            # Save original file
            with open(original_file_path, 'wb') as file:
                file.write(binary_data)
            
            # AUTOMATICALLY delete encrypted file after successful decryption
            os.remove(encrypted_file_path)
            
            return original_name
            
        except Exception as e:
            print(f"    Error decrypting {encrypted_file_path}: {str(e)}")
            return None
    
    def decrypt_text(self, text):
        """Decrypt text using character substitution"""
        decrypted_chars = []
        
        for char in text:
            if char in self.decryption_map:
                decrypted_chars.append(self.decryption_map[char])
            else:
                decrypted_chars.append(char)
        
        return ''.join(decrypted_chars)
    
    def format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes >= 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        elif size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes} bytes"
    
    def decrypt_drive(self, drive_path):
        """Decrypt all encrypted files on the selected drive"""
        print(f"🔍 Scanning drive {drive_path} for encrypted files...")
        
        try:
            # Get all encrypted files recursively
            encrypted_files, total_folders = self.get_encrypted_files(drive_path)
            
            if not encrypted_files:
                print(f"    No encrypted files found on drive {drive_path}")
                return 0, 0, 0
            
            total_files = len(encrypted_files)
            processed_files = 0
            successful_decryptions = 0
            failed_decryptions = 0
            
            print(f"    Found {total_files} encrypted files in {total_folders} folders")
            
            start_time = time.time()
            
            for file_path in encrypted_files:
                encrypted_filename = os.path.basename(file_path)
                folder_path = os.path.dirname(file_path)
                
                try:
                    # Show progress every 100 files
                    if processed_files % 100 == 0 and processed_files > 0:
                        elapsed_time = time.time() - start_time
                        files_per_second = processed_files / elapsed_time if elapsed_time > 0 else 0
                        print(f"    Progress: {processed_files}/{total_files} files ({files_per_second:.1f} files/sec)")
                    
                    # Decrypt the file and restore original (automatically delete encrypted file)
                    original_name = self.decrypt_and_restore_file(file_path)
                    if original_name:
                        successful_decryptions += 1
                    else:
                        failed_decryptions += 1
                    
                except Exception as e:
                    failed_decryptions += 1
                    print(f"    ❌ Failed to decrypt {encrypted_filename}: {str(e)}")
                
                processed_files += 1
            
            # Final statistics
            elapsed_time = time.time() - start_time
            print(f"    ✅ Drive {drive_path} completed: {successful_decryptions}/{total_files} files decrypted successfully")
            print(f"    🗑️  All encrypted files have been automatically deleted")
            print(f"    ⏱️  Time taken: {elapsed_time:.2f} seconds")
            
            return successful_decryptions, total_files, total_folders
            
        except Exception as e:
            print(f"    ❌ Error processing drive {drive_path}: {str(e)}")
            return 0, 0, 0
    
    def start_automated_decryption(self):
        """Start automated decryption of all available drives (except C:)"""
        print("🚀 Starting Automated Drive Decryption")
        print("=" * 50)
        print("🔓 This will decrypt ALL encrypted files on all drives except C:\\")
        print("📂 D: drive and all other drives WILL be processed")
        print("🗑️  Encrypted files will be automatically deleted after successful decryption")
        print("=" * 50)
        
        # Get available drives (excluding only C:)
        drives = self.get_available_drives()
        
        if not drives:
            print("❌ No drives found to decrypt (excluding only C:\\)")
            return
        
        print(f"📁 Found {len(drives)} drive(s) to decrypt: {', '.join(drives)}")
        print()
        
        # Countdown before starting
        print("🔄 Starting decryption in 5 seconds...")
        for i in range(5, 0, -1):
            print(f"    {i}...")
            time.sleep(1)
        
        print()
        print("🔓 Beginning decryption process...")
        print()
        
        total_successful = 0
        total_files = 0
        total_folders = 0
        total_drives_processed = 0
        
        # Decrypt each drive
        for drive_path in drives:
            print(f"\n💾 Processing drive: {drive_path}")
            print("-" * 40)
            
            successful, files, folders = self.decrypt_drive(drive_path)
            
            total_successful += successful
            total_files += files
            total_folders += folders
            
            if files > 0:
                total_drives_processed += 1
            
            print()
        
        # Final summary
        print("=" * 50)
        print("🎉 DECRYPTION COMPLETE!")
        print("=" * 50)
        print(f"📊 Summary:")
        print(f"   • Drives processed: {total_drives_processed}")
        print(f"   • Total folders scanned: {total_folders}")
        print(f"   • Total encrypted files found: {total_files}")
        print(f"   • Successfully decrypted: {total_successful}")
        print(f"   • Failed: {total_files - total_successful}")
        print(f"   • Encrypted files deleted: {total_successful}")
        print()
        print("✅ All original files have been restored")
        print("🗑️  All encrypted files have been automatically deleted")

def main():
    """Main function to start automated decryption"""
    try:
        decryptor = AutomatedDriveDecryptor()
        decryptor.start_automated_decryption()
    except KeyboardInterrupt:
        print("\n\n❌ Decryption process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()