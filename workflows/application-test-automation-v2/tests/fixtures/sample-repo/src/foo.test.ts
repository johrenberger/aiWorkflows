import { greet } from "./foo";

test("greets", () => {
  expect(greet("world")).toBe("hello world");
});

