package dev.polyglot.template;

import net.jqwik.api.ForAll;
import net.jqwik.api.Property;

class MathOpsProperties {
  @Property
  boolean additionIsCommutative(@ForAll int left, @ForAll int right) {
    return MathOps.add(left, right) == MathOps.add(right, left);
  }
}
