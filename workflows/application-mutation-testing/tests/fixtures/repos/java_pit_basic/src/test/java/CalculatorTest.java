package com.example;

import org.junit.Test;
import static org.junit.Assert.*;

public class CalculatorTest {
    @Test
    public void add_two_and_three_is_five() {
        assertEquals(5, new Calculator().add(2, 3));
    }

    @Test
    public void sub_three_from_two_is_negative_one() {
        assertEquals(-1, new Calculator().sub(2, 3));
    }

    @Test
    public void mul_two_and_three_is_six() {
        assertEquals(6, new Calculator().mul(2, 3));
    }

    @Test
    public void isPositive_returns_true_for_positive() {
        assertTrue(new Calculator().isPositive(1));
    }

    @Test
    public void isPositive_returns_false_for_zero() {
        assertFalse(new Calculator().isPositive(0));
    }

    @Test
    public void isPositive_returns_false_for_negative() {
        assertFalse(new Calculator().isPositive(-1));
    }
}
