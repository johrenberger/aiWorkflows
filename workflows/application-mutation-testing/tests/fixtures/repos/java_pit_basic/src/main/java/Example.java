package com.example;

// Example.java was the original minimal PIT-detected fixture. Kept
// here so the existing `test_given_pom_with_pit_when_tool_detection_runs_then_pit_detected`
// test continues to work (it only checks for "pitest" in the pom,
// not that Example is the only source). The richer Calculator +
// CalculatorTest are what PIT actually mutates.
public class Example {
    public boolean positive(int value) {
        return value > 0;
    }
}
