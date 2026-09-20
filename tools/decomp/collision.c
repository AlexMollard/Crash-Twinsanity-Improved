/* A C rewrite of the engine's segment-against-triangle test, for checking against the real thing.
 *
 * On the disc this is two functions that Ghidra shows as unrelated. SegmentTriangleDistances (0x293340)
 * computes on VU0 and returns only two floats through memory; ReadEdgeTestsFromVu0 (0x2933E4) then reads six
 * more results straight out of VU0 registers vf17, vf18, vf22, vf23, vf27 and vf28, which the first call left
 * behind. They are one routine wearing two hats, and a rewrite has to fuse them - which is the first thing
 * this experiment was meant to find out.
 *
 * Everything here follows the machine code operation for operation, because the point is bit-equality, not
 * mathematical equivalence:
 *
 *   - a cross product is VOPMULA/VOPMSUB, which computes all three lanes from the *original* register
 *     contents even when the destination is one of the sources;
 *   - a dot product is VMUL.xyz then VADDy.x then VADDz.x, so it sums as (x + y) + z and not in some other
 *     order, and float addition is not associative;
 *   - the subtractions are .xyz, so w is never touched and never read.
 *
 * VU0 is not quite IEEE-754: it flushes denormals to zero and clamps instead of producing infinities or NaN.
 * For ordinary level geometry neither difference can arise, so plain float should agree exactly. Whether it
 * does is the experiment.
 *
 *   clang -O2 -o collision collision.c   (then feed it cases on stdin; see tools/decomp/collision_test.py)
 */
#include <stdio.h>
#include <string.h>

typedef struct { float x, y, z, w; } Vec4;

/* vsub.xyz */
static Vec4 sub3(Vec4 a, Vec4 b)
{
    Vec4 r;
    r.x = a.x - b.x;
    r.y = a.y - b.y;
    r.z = a.z - b.z;
    r.w = 0.0f;
    return r;
}

/* VOPMULA ACC, a, b followed by VOPMSUB d, b, a - the PS2's cross product idiom. */
static Vec4 cross3(Vec4 a, Vec4 b)
{
    Vec4 r;
    r.x = a.y * b.z - b.y * a.z;
    r.y = a.z * b.x - b.z * a.x;
    r.z = a.x * b.y - b.x * a.y;
    r.w = 0.0f;
    return r;
}

/* VMUL.xyz then VADDy.x then VADDz.x: the sum order is (x + y) + z and it matters. */
static float dot3(Vec4 a, Vec4 b)
{
    float x = a.x * b.x;
    float y = a.y * b.y;
    float z = a.z * b.z;
    float s = x + y;
    return s + z;
}

/* distances[0..1] are the signed distances of each endpoint from the triangle's plane.
 * edges[0..5] are the six scalar triple products the original leaves in VU0, in the order it stores them. */
void SegmentTriangleTests(const Vec4 *p1, const Vec4 *p2, const Vec4 tri[3],
                          float distances[2], float edges[6])
{
    Vec4 P1 = *p1, P2 = *p2;
    Vec4 v1 = tri[0], v2 = tri[1], v3 = tri[2];

    Vec4 dir   = sub3(P2, P1);                  /* vf7  */
    Vec4 e_a   = sub3(v2, v1);                  /* vf10 and vf15 */
    Vec4 e_b   = sub3(v3, v1);                  /* vf11 before it is overwritten */
    Vec4 e_v32 = sub3(v3, v2);                  /* vf20 */
    Vec4 e_v13 = sub3(v1, v3);                  /* vf25 */

    Vec4 normal = cross3(e_a, e_b);             /* vf11 */
    Vec4 c_a    = cross3(dir, e_a);             /* vf16 */
    Vec4 c_32   = cross3(dir, e_v32);           /* vf21 */
    Vec4 c_13   = cross3(dir, e_v13);           /* vf26 */

    distances[0] = dot3(sub3(P1, v1), normal);  /* vf12 */
    distances[1] = dot3(sub3(P2, v1), normal);  /* vf13 */

    edges[0] = dot3(sub3(v1, P1), c_a);         /* vf17 */
    edges[1] = dot3(sub3(v3, P1), c_a);         /* vf18 */
    edges[2] = dot3(sub3(v2, P1), c_32);        /* vf22 */
    edges[3] = dot3(sub3(v1, P1), c_32);        /* vf23 */
    edges[4] = dot3(sub3(v3, P1), c_13);        /* vf27 */
    edges[5] = dot3(sub3(v2, P1), c_13);        /* vf28 */
}

/* RayTriangleIntersect's verdict, which is what the game actually asks for: the segment must cross the plane,
 * and neither endpoint pair of any edge test may sit clearly on the same side. The epsilon is the original's. */
int SegmentHitsTriangle(const float distances[2], const float edges[6])
{
    const float eps = 0.0001f;
    int i;
    if (!(distances[0] * distances[1] <= -eps)) return 0;
    for (i = 0; i < 6; i += 2) {
        if (!(edges[i] <= eps || edges[i + 1] <= eps)) return 0;
        if (!(-eps <= edges[i] || -eps <= edges[i + 1])) return 0;
    }
    return 1;
}

/* Cases arrive on stdin as 20 hex words - p1, p2 and the three vertices - and the answers go out the same
 * way, so the comparison is over bit patterns rather than anything a printf might round. */
int main(void)
{
    unsigned w[20];
    char line[512];

    while (fgets(line, sizeof line, stdin)) {
        int i;
        char *p = line;
        for (i = 0; i < 20; i++) {
            if (sscanf(p, "%8x", &w[i]) != 1) return i == 0 ? 0 : 1;
            p += 9;
        }
        Vec4 p1, p2, tri[3];
        memcpy(&p1, w, 16);
        memcpy(&p2, w + 4, 16);
        memcpy(tri, w + 8, 48);

        float distances[2], edges[6];
        unsigned out[8];
        SegmentTriangleTests(&p1, &p2, tri, distances, edges);
        memcpy(out, distances, 8);
        memcpy(out + 2, edges, 24);
        for (i = 0; i < 8; i++) printf("%08x ", out[i]);
        printf("%d\n", SegmentHitsTriangle(distances, edges));
    }
    return 0;
}
