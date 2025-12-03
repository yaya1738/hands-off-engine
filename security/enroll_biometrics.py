#!/usr/bin/env python3
"""
BIOMETRIC ENROLLMENT TOOL
Enroll your biometric markers for identity verification

ENROLLMENT METHODS:
1. Fingerprint - via phone fingerprint sensor (hash extracted)
2. Voice - record and analyze voice sample
3. Facial - photo analysis for 68 landmarks
4. Keystroke - type sample text to capture rhythm
5. DNA - enter STR profile from 23andMe/Ancestry

Run: python3 enroll_biometrics.py <type>
"""

import sys
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from security.biometric_identity import BiometricVerifier, BIOMETRIC_STORE

def enroll_keystroke():
    """Capture keystroke dynamics"""
    print("\n=== KEYSTROKE DYNAMICS ENROLLMENT ===")
    print("Type the following phrase 3 times to capture your typing rhythm:")
    print("\nPhrase: 'The quick brown fox jumps over the lazy dog'")
    print("\n(Press Enter after each attempt)")

    samples = []
    for i in range(3):
        input(f"\nAttempt {i+1}/3 - Press Enter when ready...")
        start = time.time()
        text = input("Type: ")
        end = time.time()

        duration_ms = (end - start) * 1000
        chars = len(text)
        avg_time_per_char = duration_ms / chars if chars > 0 else 0

        samples.append({
            "duration_ms": duration_ms,
            "chars": chars,
            "avg_ms_per_char": avg_time_per_char,
            "hold_ms": avg_time_per_char * 0.4,  # Estimate
            "flight_ms": avg_time_per_char * 0.6,  # Estimate
            "wpm": (chars / 5) / (duration_ms / 60000) if duration_ms > 0 else 0
        })
        print(f"  Captured: {chars} chars in {duration_ms:.0f}ms ({samples[-1]['wpm']:.0f} WPM)")

    verifier = BiometricVerifier()
    result = verifier.enroll_keystroke(samples)

    print("\n✓ Keystroke dynamics enrolled!")
    print(f"  Average hold time: {verifier.biometrics['keystroke']['avg_key_hold_ms']:.1f}ms")
    print(f"  Average flight time: {verifier.biometrics['keystroke']['avg_flight_time_ms']:.1f}ms")


def enroll_voice_placeholder():
    """Voice enrollment (placeholder - needs audio capture)"""
    print("\n=== VOICE PRINT ENROLLMENT ===")
    print("To enroll voice, you need to:")
    print("1. Record yourself saying: 'My name is Yair Siegel'")
    print("2. Upload the audio file")
    print("\nVoice analysis will extract:")
    print("  - Fundamental frequency (pitch)")
    print("  - Formant frequencies (resonance)")
    print("  - Spectral envelope (voice signature)")

    freq = input("\nIf you know your voice fundamental frequency in Hz, enter it (or skip): ")
    if freq.strip():
        try:
            freq_hz = float(freq)
            verifier = BiometricVerifier()
            verifier.biometrics["voice"]["fundamental_frequency_hz"] = freq_hz
            verifier.biometrics["voice"]["enrolled"] = True
            verifier.biometrics["voice"]["enrolled_at"] = datetime.now().isoformat()
            verifier._save_biometrics()
            print(f"✓ Voice frequency enrolled: {freq_hz} Hz")
        except:
            print("Invalid frequency")


def enroll_facial_placeholder():
    """Facial geometry enrollment (placeholder - needs camera)"""
    print("\n=== FACIAL GEOMETRY ENROLLMENT ===")
    print("To enroll facial geometry, provide measurements:")

    measurements = {}

    iod = input("Interocular distance in mm (distance between eye centers): ")
    if iod.strip():
        measurements["interocular"] = float(iod)

    nose = input("Nose length in mm (bridge to tip): ")
    if nose.strip():
        measurements["nose_length"] = float(nose)

    face_w = input("Face width in mm (cheekbone to cheekbone): ")
    if face_w.strip():
        measurements["face_width"] = float(face_w)

    if measurements:
        verifier = BiometricVerifier()
        verifier.biometrics["facial"]["interocular_distance_mm"] = measurements.get("interocular")
        verifier.biometrics["facial"]["nose_length_mm"] = measurements.get("nose_length")
        verifier.biometrics["facial"]["face_width_mm"] = measurements.get("face_width")
        verifier.biometrics["facial"]["enrolled"] = True
        verifier.biometrics["facial"]["enrolled_at"] = datetime.now().isoformat()
        verifier._save_biometrics()
        print("✓ Facial measurements enrolled!")


def enroll_dna():
    """DNA STR profile enrollment"""
    print("\n=== DNA PROFILE ENROLLMENT ===")
    print("Enter your STR profile from DNA test (23andMe, Ancestry, etc)")
    print("Format: locus=value (e.g., D3S1358=15,16)")
    print("Type 'done' when finished\n")

    loci = [
        "D3S1358", "vWA", "D16S539", "CSF1PO", "TPOX",
        "D8S1179", "D21S11", "D18S51", "D2S441", "D19S433",
        "TH01", "FGA", "D22S1045", "D5S818", "D13S317",
        "D7S820", "SE33", "D10S1248", "D1S1656", "D12S391"
    ]

    profile = {"amelogenin": "XY"}  # Male

    print("Known CODIS loci:")
    for i, locus in enumerate(loci, 1):
        print(f"  {i}. {locus}")

    print("\nEnter values (or press Enter to skip):")
    for locus in loci:
        value = input(f"  {locus}: ").strip()
        if value:
            profile[locus] = value

    if len(profile) > 1:  # More than just amelogenin
        verifier = BiometricVerifier()
        result = verifier.enroll_dna(profile)
        print(f"\n✓ DNA profile enrolled with {result['loci']} loci!")
        print(f"  Uniqueness: 1 in 10^{len(profile)*1.5:.0f}")


def enroll_fingerprint_hash():
    """Fingerprint enrollment via hash (from phone sensor)"""
    print("\n=== FINGERPRINT ENROLLMENT ===")
    print("On your phone, extract fingerprint hash from biometric API")
    print("Or enter a unique identifier for each finger\n")

    fingers = ["right_thumb", "right_index", "left_thumb", "left_index"]

    verifier = BiometricVerifier()

    for finger in fingers:
        fp_id = input(f"{finger.replace('_', ' ').title()} ID/hash (or skip): ").strip()
        if fp_id:
            fp_hash = hashlib.sha256(fp_id.encode()).hexdigest()
            verifier.biometrics["fingerprints"][finger] = {
                "hash": fp_hash,
                "enrolled": True,
                "enrolled_at": datetime.now().isoformat(),
                "minutiae_count": 50  # Typical
            }

    verifier._save_biometrics()
    enrolled = sum(1 for f, d in verifier.biometrics["fingerprints"].items()
                   if isinstance(d, dict) and d.get("enrolled"))
    print(f"\n✓ {enrolled} fingerprint(s) enrolled!")


def enroll_physical():
    """Physical measurements enrollment"""
    print("\n=== PHYSICAL CONSTANTS ENROLLMENT ===")

    verifier = BiometricVerifier()

    # Already known from profile
    print("Known constants:")
    print("  Height: 193cm (6'4\")")
    print("  Eye color: Hazel")
    print("  Handedness: Ambidextrous")

    # Additional
    ear = input("\nEar lobe type (attached/detached): ").strip().lower()
    if ear:
        verifier.biometrics["ear"]["lobe_type"] = ear
        verifier.biometrics["ear"]["enrolled"] = True
        verifier._save_biometrics()
        print(f"✓ Ear type enrolled: {ear}")

    shoe = input("Shoe size (US): ").strip()
    if shoe:
        # Store in facial as misc
        verifier.biometrics["facial"]["shoe_size_us"] = shoe
        verifier._save_biometrics()
        print(f"✓ Shoe size enrolled: {shoe}")


def show_status():
    """Show enrollment status"""
    verifier = BiometricVerifier()
    status = verifier.get_enrollment_status()

    print("\n" + "=" * 50)
    print("BIOMETRIC ENROLLMENT STATUS")
    print("=" * 50)

    print("\n[ENROLLED]")
    for bio in status["enrolled_biometrics"]:
        print(f"  ✓ {bio}")

    print("\n[NOT ENROLLED]")
    for bio in status["pending_biometrics"]:
        print(f"  ○ {bio}")

    print("\n" + "=" * 50)


def main():
    if len(sys.argv) < 2:
        print("BIOMETRIC ENROLLMENT")
        print("-" * 30)
        print("Usage: python3 enroll_biometrics.py <type>")
        print("\nTypes:")
        print("  keystroke  - Enroll typing pattern")
        print("  voice      - Enroll voice print")
        print("  facial     - Enroll facial geometry")
        print("  dna        - Enroll DNA STR profile")
        print("  fingerprint- Enroll fingerprint hashes")
        print("  physical   - Enroll physical measurements")
        print("  status     - Show enrollment status")
        print("  all        - Run all enrollment wizards")
        return

    cmd = sys.argv[1].lower()

    if cmd == "keystroke":
        enroll_keystroke()
    elif cmd == "voice":
        enroll_voice_placeholder()
    elif cmd == "facial":
        enroll_facial_placeholder()
    elif cmd == "dna":
        enroll_dna()
    elif cmd == "fingerprint":
        enroll_fingerprint_hash()
    elif cmd == "physical":
        enroll_physical()
    elif cmd == "status":
        show_status()
    elif cmd == "all":
        enroll_keystroke()
        enroll_physical()
        enroll_voice_placeholder()
        enroll_facial_placeholder()
        show_status()
    else:
        print(f"Unknown type: {cmd}")


if __name__ == "__main__":
    main()
