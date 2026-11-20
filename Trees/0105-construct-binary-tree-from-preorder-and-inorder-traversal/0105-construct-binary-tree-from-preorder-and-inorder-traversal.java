/**
 * Definition for a binary tree node.
 * public class TreeNode {
 *     int val;
 *     TreeNode left;
 *     TreeNode right;
 *     TreeNode() {}
 *     TreeNode(int val) { this.val = val; }
 *     TreeNode(int val, TreeNode left, TreeNode right) {
 *         this.val = val;
 *         this.left = left;
 *         this.right = right;
 *     }
 * }
 */
class Solution{
    int preIndex=0;
    Map<Integer,Integer>map=new HashMap<>();
    public TreeNode buildTree(int[] preorder,int[] inorder) {
        for (int i=0;i<inorder.length;i++) {
            map.put(inorder[i],i);
        }
        return solve(preorder,0,inorder.length-1);
    }
    public TreeNode solve(int[] preorder,int start,int end) {
        if (start > end) {
            return null;
        }
        int value=preorder[preIndex++];
        TreeNode root=new TreeNode(value);
        int index=map.get(value);
        root.left=solve(preorder,start,index-1);
        root.right=solve(preorder,index+1,end);
        return root;
    }
}