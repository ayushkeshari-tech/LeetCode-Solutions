import java.util.*;
class Solution {
    HashMap<Integer, Integer> map = new HashMap<>();
    int max = 0;
    public int[] findFrequentTreeSum(TreeNode root) {
        calculateSum(root);
        ArrayList<Integer> list = new ArrayList<>();
        for (int sum : map.keySet()) {
            if (map.get(sum) == max) {
                list.add(sum);
            }
        }

        int[] ans = new int[list.size()];

        for (int i = 0; i < list.size(); i++) {
            ans[i] = list.get(i);
        }

        return ans;
    }

    public int calculateSum(TreeNode root) {
        if (root == null) {
            return 0;
        }

        int left = calculateSum(root.left);
        int right = calculateSum(root.right);

        int total = root.val + left + right;

        map.put(total, map.getOrDefault(total, 0) + 1);

        max = Math.max(max, map.get(total));

        return total;
    }
}
