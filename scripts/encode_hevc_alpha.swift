#!/usr/bin/env swift

// Encodes PNG frame sequences into HEVC-with-alpha .mov files using AVFoundation.
// Usage: swift encode_hevc_alpha.swift <frames_dir> <output.mov> [fps]

import AVFoundation
import AppKit
import Foundation
import VideoToolbox

guard CommandLine.arguments.count >= 3 else {
    print("Usage: encode_hevc_alpha.swift <frames_dir> <output.mov> [fps]")
    exit(1)
}

let framesDir = CommandLine.arguments[1]
let outputPath = CommandLine.arguments[2]
let fps = CommandLine.arguments.count > 3 ? Int(CommandLine.arguments[3]) ?? 24 : 24

// Gather sorted frame files
let fm = FileManager.default
let files = try fm.contentsOfDirectory(atPath: framesDir)
    .filter { $0.hasSuffix(".png") }
    .sorted()

guard !files.isEmpty else {
    print("No PNG files found in \(framesDir)")
    exit(1)
}

print("Found \(files.count) frames, encoding at \(fps) fps...")

// Load first frame to get dimensions
let firstPath = (framesDir as NSString).appendingPathComponent(files[0])
guard let firstImage = NSImage(contentsOfFile: firstPath),
      let firstRep = firstImage.representations.first as? NSBitmapImageRep else {
    print("Failed to load first frame")
    exit(1)
}

let width = firstRep.pixelsWide
let height = firstRep.pixelsHigh
print("Frame size: \(width)x\(height)")

// Remove existing output
let outputURL = URL(fileURLWithPath: outputPath)
try? fm.removeItem(at: outputURL)

// Create asset writer
let writer = try AVAssetWriter(outputURL: outputURL, fileType: .mov)

// HEVC with alpha settings
let videoSettings: [String: Any] = [
    AVVideoCodecKey: AVVideoCodecType.hevcWithAlpha,
    AVVideoWidthKey: width,
    AVVideoHeightKey: height,
    AVVideoCompressionPropertiesKey: [
        AVVideoAverageBitRateKey: 8_000_000,
    ] as [String: Any],
]

let writerInput = AVAssetWriterInput(mediaType: .video, outputSettings: videoSettings)
writerInput.expectsMediaDataInRealTime = false

let sourcePixelBufferAttributes: [String: Any] = [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
    kCVPixelBufferWidthKey as String: width,
    kCVPixelBufferHeightKey as String: height,
]

let adaptor = AVAssetWriterInputPixelBufferAdaptor(
    assetWriterInput: writerInput,
    sourcePixelBufferAttributes: sourcePixelBufferAttributes
)

writer.add(writerInput)
writer.startWriting()
writer.startSession(atSourceTime: .zero)

let frameDuration = CMTime(value: 1, timescale: CMTimeScale(fps))

for (index, file) in files.enumerated() {
    let filePath = (framesDir as NSString).appendingPathComponent(file)

    autoreleasepool {
        guard let image = NSImage(contentsOfFile: filePath),
              let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
            print("Failed to load frame: \(file)")
            return
        }

        var pixelBuffer: CVPixelBuffer?
        let status = CVPixelBufferCreate(
            kCFAllocatorDefault,
            width, height,
            kCVPixelFormatType_32BGRA,
            sourcePixelBufferAttributes as CFDictionary,
            &pixelBuffer
        )

        guard status == kCVReturnSuccess, let buffer = pixelBuffer else {
            print("Failed to create pixel buffer for frame \(index)")
            return
        }

        CVPixelBufferLockBaseAddress(buffer, [])
        let context = CGContext(
            data: CVPixelBufferGetBaseAddress(buffer),
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: CVPixelBufferGetBytesPerRow(buffer),
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue
        )

        // Clear to transparent
        context?.clear(CGRect(x: 0, y: 0, width: width, height: height))
        context?.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))
        CVPixelBufferUnlockBaseAddress(buffer, [])

        let presentationTime = CMTime(value: CMTimeValue(index), timescale: CMTimeScale(fps))

        while !writerInput.isReadyForMoreMediaData {
            Thread.sleep(forTimeInterval: 0.01)
        }

        adaptor.append(buffer, withPresentationTime: presentationTime)
    }

    if (index + 1) % 60 == 0 {
        print("  Encoded \(index + 1)/\(files.count) frames...")
    }
}

writerInput.markAsFinished()

let semaphore = DispatchSemaphore(value: 0)
writer.finishWriting {
    semaphore.signal()
}
semaphore.wait()

if writer.status == .completed {
    let fileSize = (try? fm.attributesOfItem(atPath: outputPath)[.size] as? Int) ?? 0
    print("Done! Output: \(outputPath) (\(fileSize / 1024) KB)")
} else {
    print("Encoding failed: \(writer.error?.localizedDescription ?? "unknown error")")
    exit(1)
}
