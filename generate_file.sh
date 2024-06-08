#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <size> <unit>"
    echo "Example: $0 100 MB"
    exit 1
fi

# Check if the input size is a valid number
if ! [[ $1 =~ ^[0-9]+$ ]]; then
    echo "Error: Input size must be a positive integer."
    exit 1
fi

# Check if the unit is valid
unit=$(echo "$2" | tr '[:upper:]' '[:lower:]')
if [ "$unit" != "kb" ] && [ "$unit" != "mb" ] && [ "$unit" != "gb" ] && [ "$unit" != "b" ]; then
    echo "Error: Invalid unit. Please use KB, MB, GB, or B."
    exit 1
fi

# Convert the input size to bytes
size=$1
case $unit in
    "kb")
        size_in_bytes=$((size * 1024))
        ;;
    "mb")
        size_in_bytes=$((size * 1024 * 1024))
        ;;
    "gb")
        size_in_bytes=$((size * 1024 * 1024 * 1024))
        ;;
    "b")
        size_in_bytes=$size
        ;;
esac

# Generate the file
output_file="output_file_${size}${unit}.txt"

echo "Generating a text file of size $size $unit..."

# Create a sparse file with the desired size
truncate -s $size_in_bytes "$output_file"

# Fill the file with text content
text_content="Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n"
echo -ne "$text_content" >> "$output_file"

echo "Text file $output_file created successfully."
