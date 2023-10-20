import tkinter as tk
from PIL import Image, ImageTk


def main():
	# Create a Tkinter root window
	root = tk.Tk()

	# Load the image
	image = Image.open("img/grass128.png")

	# Create a PhotoImage object
	image_tk = ImageTk.PhotoImage(image)

	# Create a Label widget to display the image
	label = tk.Label(root, image=image_tk)
	label.pack()

	# Start the Tkinter mainloop
	root.mainloop()


if __name__ == '__main__':
	main()
