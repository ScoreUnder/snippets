// This is related to Tsuro
// The OEIS has calculated more than I can with this tool: https://oeis.org/A132105
import scala.collection.mutable.{HashSet, Set}
type Conn = IndexedSeq[Int]  // Connections array type
val connections = if (args.length > 0) args(0).toInt else 8
def isRotation(arr: Conn, all: Set[Conn]): Boolean = {
    val rotations = connections / 2 - 1
    for (n <- 0 to rotations) {
        val rot = (arr.drop(n*2) ++ arr.take(n*2)) map { v =>
            (connections + v - 2 * n) % connections
        }
        if (all contains rot)
            return true
    }
    false
}
def isOk(arr: Conn): Boolean = {
    for ((v, i) <- arr.zipWithIndex) {
        if (i == v || arr(v) != i)
            return false
    }
    true
}
val okSeqs = HashSet[Conn]()
for (arr <- (0 until connections).permutations) {
    if (isOk(arr) && !isRotation(arr, okSeqs)) {
        okSeqs += arr
    }
}
println(s"Found: ${okSeqs.size}")
