sig A {}

pred sat_example {
  some A
}

pred unsat_example {
  #A > 1
}

run sat_example for 1
run unsat_example for 1

