#!/bin/bash

output_file="concatenated_files.txt"
ignore_dir=""
file_extensions=()

# Extract the ignore directory argument if provided
while [[ $# -gt 0 ]]; do
    case $1 in
        --ignore-dir)
            ignore_dir="$2"
            shift 2
            ;;
        *)
            file_extensions+=("$1")
            shift
            ;;
    esac
done

# Check if file extensions are provided
if [ ${#file_extensions[@]} -eq 0 ]; then
    echo "Usage: $0 [--ignore-dir <directory_to_ignore>] <file_extension1> [<file_extension2> ...]"
    exit 1
fi

# Remove existing output file
rm -f "$output_file"

# Function to recursively concatenate files with the specified extensions
concatenate_files() {
    local directory="$1"
    
    # If the current directory matches the ignore directory, skip it
    if [ "$directory" = "$ignore_dir" ]; then
        return
    fi

    # Loop through each item in the directory
    for item in "$directory"/*; do
        # Check if it's a file with one of the specified extensions
        if [ -f "$item" ]; then
            file_extension="${item##*.}"
            for ext in "${file_extensions[@]}"; do
                if [ "$file_extension" = "$ext" ]; then
                    # Concatenate file path and content into the output file
                    echo "File: $item" >> "$output_file"
                    echo "" >> "$output_file"  # Separate file path and content
                    cat "$item" >> "$output_file"
                    echo "" >> "$output_file"  # Separate files
                    echo "---------------------------------------------" >> "$output_file"
                    break
                fi
            done
        elif [ -d "$item" ]; then
            # If it's a directory, recursively call this function
            concatenate_files "$item"
        fi
    done
}

# Start concatenating from the current directory
concatenate_files "."

echo "Concatenation completed. Output saved to: $output_file"